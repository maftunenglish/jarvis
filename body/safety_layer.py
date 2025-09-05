# body/safety_layer.py

def confirm_destructive_action(action_description):
    """
    Requests user confirmation for potentially dangerous actions.
    
    Args:
        action_description (str): Description of what will be done
        
    Returns:
        bool: True if confirmed, False if cancelled
    """
    print(f"⚠️  Safety Check: {action_description}")
    response = input("Confirm? (yes/no): ").lower().strip()
    return response in ['y', 'yes', 'confirm']