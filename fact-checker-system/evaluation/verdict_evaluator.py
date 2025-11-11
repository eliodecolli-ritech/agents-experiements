from deepeval import evaluate

# Example function to evaluate a verdict

def evaluate_verdict(prediction: str, ground_truth: str):
    """
    Evaluate the LLM's verdict against the ground truth using DeepEval.
    Args:
        prediction (str): The verdict from your agent (e.g., 'TRUE', 'FALSE', etc.)
        ground_truth (str): The expected verdict label
    Returns:
        DeepEval result object
    """
    result = evaluate(
        prediction=prediction,
        ground_truth=ground_truth,
        task_type="fact-checking"
    )
    return result

# Example usage
if __name__ == "__main__":
    pred = "TRUE"
    gt = "TRUE"
    eval_result = evaluate_verdict(pred, gt)
    print(eval_result)
