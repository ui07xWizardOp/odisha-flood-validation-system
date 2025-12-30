from typing import Dict, Any

class ReputationSystem:
    """
    Layer 3: User Reputation System.
    Manages trust scores using Bayesian updates.
    """
    
    TRUST_INCREMENT = 0.1   # Bonus for verified report
    TRUST_DECREMENT = 0.15  # Penalty for false alarm
    
    def __init__(self):
        # In a real app, this would connect to the DB
        pass

    def get_trust_score(self, user_id: int, db_connection=None) -> float:
        """
        Retrieves user trust score. 
        MOCK implementation usually returns from DB.
        """
        # TODO: Replace with DB call
        # cursor.execute("SELECT trust_score FROM users WHERE user_id = %s", (user_id,))
        # return cursor.fetchone()[0]
        
        # For now, return a default neutral score if we can't fetch
        return 0.5

    def validate(self, user_id: int) -> Dict[str, Any]:
        """
        Returns validation weight based on user trust.
        """
        try:
            trust_score = self.get_trust_score(user_id)
        except Exception:
            trust_score = 0.5
            
        return {
            'layer3_score': float(trust_score)
        }
        
    def update_trust_score(self, user_id: int, report_outcome: str, current_score: float) -> float:
        """
        Updates trust score based on report validation outcome.
        
        Args:
            report_outcome: 'validated' or 'flagged'
        """
        new_score = current_score
        
        if report_outcome == 'validated':
            new_score += self.TRUST_INCREMENT
        elif report_outcome == 'flagged':
            new_score -= self.TRUST_DECREMENT
            
        # Clamp between 0 and 1
        return max(0.0, min(1.0, new_score))
