# Reinforcement Learning - Summary

## Value-Based Reinforcement Learning

### Technical Details

1. **Markov Decision Process (MDP):**
    - **Components:**
        - States (`S`): A set of possible states.
        - Actions (`A`): A set of possible actions.
        - Transition Function (`T`): Probability of reaching a state `s'` from state `s` by performing action `a`.
        - Reward Function (`R`): Immediate reward received after performing action `a` in state `s`.
        - Discount Factor (`γ`): A measure of how future rewards are valued compared to immediate rewards.
        - Horizon (`H`): Number of decisions to make.

2. **Value Iteration:**
   - To find the optimal policy, the value function is computed iteratively:
   - **Python Code:** 
     ```python
     def value_iteration(states, actions, T, R, gamma, theta=0.001):
         V = np.zeros(len(states))  # Initializing value function
         while True:
             delta = 0
             for s in states:
                 v = V[s]
                 V[s] = max(sum(T(s, a, s_prime) * (R(s, a) + gamma * V[s_prime]) for s_prime in states) for a in actions)
                 delta = max(delta, abs(v - V[s]))
             if delta < theta:
                 break
         return V
     ```
   - **Explanation:** The function calculates the value function `V` by considering all possible actions and transitions, updating until convergence based on a small threshold `theta`.

3. **Policy Iteration:**
   - Alternates between policy evaluation and policy improvement:
   - **Python Code:** 
     ```python
     def policy_iteration(states, actions, T, R, gamma):
         policy = np.random.choice(actions, len(states))  # Random initial policy
         V = np.zeros(len(states))
         is_policy_stable = False

         while not is_policy_stable:
             # Policy Evaluation
             eval_delta = float('inf')
             while eval_delta > 0.001:
                 eval_delta = 0
                 for s in states:
                     v = V[s]
                     V[s] = sum(T(s, policy[s], s_prime) * (R(s, policy[s]) + gamma * V[s_prime]) for s_prime in states)
                     eval_delta = max(eval_delta, abs(v - V[s]))

             # Policy Improvement
             is_policy_stable = True
             for s in states:
                 old_action = policy[s]
                 policy[s] = max(actions, key=lambda a: sum(T(s, a, s_prime) * (R(s, a) + gamma * V[s_prime]) for s_prime in states))
                 if old_action != policy[s]:
                     is_policy_stable = False
         return policy, V
     ```
   - **Explanation:** This code evaluates the policy to find the value function and then improves the policy by choosing the best action in each state.

4. **Q-Learning:**
   - Off-policy algorithm that directly estimates the value of the optimal policy.
   - **Python Code:**
     ```python
     def q_learning(states, actions, T, R, gamma, alpha, episodes):
         Q = np.zeros((len(states), len(actions)))  # Initializing Q-table
         for _ in range(episodes):
             state = np.random.choice(states)  
             while True:
                 action = np.random.choice(actions)
                 next_state = np.random.choice(states, p=[T(state, action, s_prime) for s_prime in states])
                 reward = R(state, action)
                 Q[state, action] += alpha * (reward + gamma * np.max(Q[next_state]) - Q[state, action])
                 if termination_condition:
                     break
                 state = next_state
         return Q
     ```
   - **Explanation:** In this code, `Q` values are iteratively updated based on experienced rewards and estimated future rewards, learning the policy off-line.

### Extensions

1. **Function Approximation:** 
   - Tackles large state-action spaces by using linear approximators or neural networks to estimate value functions.

2. **Deep Q-Learning (DQN):**
   - Utilizes experience replay for stable training and a target network to reduce correlation between consecutive updates.

## Policy-Search Approaches

### Technical Details

1. **Policy Gradient (PG) Methods:**
   - Directly optimize control policies represented by parameter vectors.
   - **Python Code for parameter updates (simplified):**
     ```python
     def policy_gradient_update(policy_params, trajectory, learning_rate):
         for state, action, reward in trajectory:
             grad_log_prob = compute_gradient(policy_params, state, action)
             policy_params += learning_rate * grad_log_prob * reward
         return policy_params
     ```
   - **Explanation:** This method updates policy parameters based on the logarithm of the probability of actions taken, weighted by rewards.

2. **Model-Based Policy Search:**
   - Combines learning of environment models with policy optimization.
   - Python-style pseudocode for iterative model learning and policy optimization.

3. **Preference-Based and Risk-Sensitive Approaches:**
   - Incorporate preferences over policies and risk considerations, using measures like quantile optimization.

### Conclusion

Reinforcement Learning techniques range from classical MDP formulations to advanced deep learning and policy-search methods, each with their own strengths and suited applications in decision-making tasks under uncertainty.

[View original paper](https://arxiv.org/abs/2005.14419)