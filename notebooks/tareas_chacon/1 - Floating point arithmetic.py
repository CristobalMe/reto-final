import math

# ==========================================
# Task 1: The Harmonic Series
# ==========================================

def harmonic_sum_forward(N):
    """
    Calculates sum(1/n) from n=1 to N.
    """
    total = 0.0
    for n in range(1, N + 1):
        total += 1.0 / n
    return total

def harmonic_sum_backward(N):
    """
    Calculates sum(1/n) from n=N down to 1.
    """
    total = 0.0
    for n in range(N, 0, -1):
        total += 1.0 / n
    return total

# ==========================================
# Task 2: Stable Variance
# ==========================================

def variance_naive(data):
    """
    Calculates variance using the unstable one-pass formula:
    Var = (Sum(x^2) / N) - (Mean)^2
    """
    N = len(data)
    if N == 0: return 0.0

    # TODO: Calculate sum of squares and mean, then apply formula
    return 0.0

def variance_stable(data):
    """
    Calculates variance using a numerically stable method
    (e.g., Two-Pass or Welford's).
    """
    N = len(data)
    if N == 0: return 0.0

    # TODO: Calculate Mean first
    # TODO: Calculate sum of squared differences from the mean
    return 0.0

# ==========================================
# Task 3: Robust Quadratic Solver
# ==========================================

def solve_quadratic(a, b, c):
    """
    Solves ax^2 + bx + c = 0 handling catastrophic cancellation.
    Returns tuple (root1, root2).
    """
    discriminant = math.sqrt(b**2 - 4*a*c)

    # TODO: Implement the logic to avoid subtracting similar numbers.
    # Hint: Check the sign of b to decide which root is 'safe' to calculate normally.
    # Then use Vieta's formulas (x1 * x2 = c/a) to find the other root.

    return (0.0, 0.0) # Placeholder return

# ==========================================
# Main Execution Block (Testing)
# ==========================================
if __name__ == "__main__":
    print("--- Task 1: Harmonic Series (N=1,000,000) ---")
    fwd = harmonic_sum_forward(1000000)
    bwd = harmonic_sum_backward(1000000)
    print(f"Forward Sum:  {fwd:.20f}")
    print(f"Backward Sum: {bwd:.20f}")
    print(f"Difference:   {abs(fwd - bwd):.20f}")

    print("\n--- Task 2: Variance Calculation ---")
    # Dataset: Large offset, small variance
    # True variance of [0.1, 0.2, 0.3] is roughly 0.0066...
    # Adding 1e9 to everything should NOT change the variance.
    test_data = [1e9 + 0.1, 1e9 + 0.2, 1e9 + 0.3]

    v_naive = variance_naive(test_data)
    v_stable = variance_stable(test_data)

    print(f"Naive Variance:  {v_naive}")
    print(f"Stable Variance: {v_stable}")

    print("\n--- Task 3: Quadratic Formula ---")
    # x^2 + 10^8x + 1 = 0. Roots are approx -10^8 and -10^-8
    a, b, c = 1.0, 10**8, 1.0
    r1, r2 = solve_quadratic(a, b, c)
    print(f"Roots for a={a}, b={b}, c={c}:")
    print(f"Root 1: {r1}")
    print(f"Root 2: {r2}")
