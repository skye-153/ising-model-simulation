# ==============================================================================
#  Quantum Spin Chain Dynamics Simulation with Animation
# ==============================================================================
#  This script simulates the time evolution of a transverse-field Ising model
#  and generates an animation of the dynamics.
# ==============================================================================

# 1. IMPORTS
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.primitives import Sampler

# ==============================================================================
#  2. DEFINE SYSTEM PARAMETERS
# ==============================================================================
num_qubits = 4
coupling_J = 1.0  # Interaction strength
field_h = 1.2     # Transverse field strength

# Animation and time parameters
total_time = 10.0
fps = 15
total_frames = int(total_time * fps)
time_step = total_time / total_frames

# ==============================================================================
#  3. THE TROTTER STEP FUNCTION
# ==============================================================================
def create_trotter_step(circuit):
    """Applies one step of the Trotterized time evolution for the Ising model."""
    # Part 1: ZZ-interaction term
    for i in range(num_qubits - 1):
        circuit.cx(i, i + 1)
        circuit.rz(2 * coupling_J * time_step, i + 1)
        circuit.cx(i, i + 1)
    circuit.barrier()
    
    # Part 2: X-field term
    for i in range(num_qubits):
        circuit.rx(2 * field_h * time_step, i)
    circuit.barrier()
    return circuit

# ==============================================================================
#  4. SET UP THE PLOT FOR ANIMATION
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [1, 3]})
fig.suptitle('Quantum Spin Chain Dynamics: Transverse-Field Ising Model', fontsize=16)

# --- Subplot 1: Spin Visualization ---
ax1.set_xlim(-1, num_qubits)
ax1.set_ylim(-1, 1)
ax1.set_xticks(range(num_qubits))
ax1.set_yticks([])
ax1.set_title('Spin Chain State')
spins = ax1.scatter(range(num_qubits), [0]*num_qubits, s=400, c=[], cmap='coolwarm', vmin=-1, vmax=1)

# --- Subplot 2: Magnetization Graph ---
ax2.set_xlim(0, total_time)
ax2.set_ylim(-1.1, 1.1)
ax2.set_xlabel('Time ($t$)')
ax2.set_ylabel('Magnetization $\\langle Z_0 \\rangle$')
ax2.grid(True, linestyle='--', alpha=0.6)
line, = ax2.plot([], [], 'o-', color='royalblue', markersize=4)
time_text = ax2.text(0.02, 0.95, '', transform=ax2.transAxes, verticalalignment='top')

# ==============================================================================
#  5. ANIMATION LOGIC
# ==============================================================================
# Initialize simulation variables
sampler = Sampler()
history_times = []
history_magnetization = []
# Start with a base circuit in the |100...> state
base_circuit = QuantumCircuit(num_qubits)
base_circuit.x(0)
base_circuit.barrier()

def update(frame):
    """This function is called for each frame of the animation."""
    global base_circuit
    
    # Evolve the circuit by one more Trotter step
    base_circuit = create_trotter_step(base_circuit)
    
    # --- Measurement ---
    # We need to measure all qubits to color the spin chain visualization
    qc_measure = base_circuit.copy()
    qc_measure.measure_all()
    
    # Run the measurement circuit
    job = sampler.run(qc_measure, shots=1024)
    result = job.result()
    prob_dist = result.quasi_dists[0].binary_probabilities()

    # --- Data Processing ---
    # Calculate magnetization for each spin to set its color
    spin_colors = np.zeros(num_qubits)
    for state, prob in prob_dist.items():
        # Qiskit returns states reversed, so we un-reverse it
        reversed_state = state[::-1] 
        for i in range(num_qubits):
            if reversed_state[i] == '0':
                spin_colors[i] += prob
            else: # state is '1'
                spin_colors[i] -= prob
    
    # Update the visualization
    spins.set_array(spin_colors)

    # Update the graph data for qubit 0
    current_time = frame * time_step
    history_times.append(current_time)
    history_magnetization.append(spin_colors[0])
    line.set_data(history_times, history_magnetization)
    time_text.set_text(f'Time = {current_time:.2f}s')
    
    print(f"Processing Frame: {frame+1}/{total_frames} | Time: {current_time:.2f}s")

    return line, spins, time_text

# Create and save the animation
ani = animation.FuncAnimation(fig, update, frames=total_frames, blit=True, interval=1000/fps)

print("\nSaving animation... This may take a few moments.")
ani.save('spin_chain_dynamics.gif', writer='pillow', fps=fps)
print("\nAnimation saved as 'spin_chain_dynamics.gif'")

plt.close(fig) # Close the plot window to prevent it from displaying after saving

