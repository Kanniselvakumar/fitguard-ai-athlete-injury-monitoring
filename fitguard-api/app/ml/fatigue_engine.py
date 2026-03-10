def calculate_fatigue(duration_hrs, heart_rate, sleep_hrs, rest_days):
    """
    Fatigue Engine calculation.
    Weighted sum of training_duration, heart_rate delta, sleep_deficit, and rest_days.
    Returns:
       score (float): 0-100 fatigue score
       level (int): 0=Low, 1=Medium, 2=High
    """
    # Assumptions/Weights for synthetic baseline
    # duration factor: 1 hr adds 10 points
    dur_factor = duration_hrs * 10
    
    # HR factor: if HR > 150, adds more strain
    hr_factor = 0
    if heart_rate:
        if heart_rate > 170: hr_factor = 20
        elif heart_rate > 150: hr_factor = 10
        elif heart_rate > 130: hr_factor = 5
        
    # Sleep deficit: less than 8 hrs adds strain
    sleep_deficit = max(0, 8 - sleep_hrs) * 5
    
    # Rest days factor: reduces strain
    rest_recovery = rest_days * (-10)
    
    # Calculate score
    score = dur_factor + hr_factor + sleep_deficit + rest_recovery
    score = max(0, min(100, score)) # clamp 0-100
    
    # Determine level mapping to 0, 1, 2
    if score > 75:
        level = 2 # High
    elif score > 40:
        level = 1 # Medium
    else:
        level = 0 # Low
        
    return score, level
