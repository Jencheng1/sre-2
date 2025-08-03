"""
Accuracy tracking for feedback loop improvement verification
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict
import numpy as np

class AccuracyTracker:
    """Track and analyze accuracy improvements from feedback"""
    
    def __init__(self):
        # In-memory storage for demo/testing
        # In production, this would use DynamoDB or similar
        self.feedback_history = defaultdict(list)
        self.baseline_accuracy = {
            "network_latency": 0.65,
            "service_outage": 0.70,
            "performance_degradation": 0.60,
            "security_incident": 0.75
        }
        
    def add_feedback_result(self, feedback: Dict[str, Any]):
        """Add a feedback result to track accuracy"""
        incident_type = feedback.get("incident_type", "unknown")
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "predicted_cause": feedback.get("predicted_cause", ""),
            "actual_cause": feedback.get("actual_cause", ""),
            "correct": feedback.get("correct", False),
            "confidence": feedback.get("confidence", 0.5),
            "time_to_resolution": feedback.get("time_to_resolution", 0)
        }
        
        self.feedback_history[incident_type].append(result)
    
    def get_accuracy_metrics(self, incident_type: str) -> Dict[str, Any]:
        """Calculate accuracy metrics for an incident type"""
        baseline = self.baseline_accuracy.get(incident_type, 0.5)
        
        history = self.feedback_history.get(incident_type, [])
        
        if not history:
            # Return baseline if no feedback yet
            return {
                "accuracy": baseline,
                "confidence": 0.5,
                "sample_size": 0,
                "improvement": 0.0,
                "trend": "stable"
            }
        
        # Calculate current accuracy
        correct_predictions = sum(1 for h in history if h["correct"])
        total_predictions = len(history)
        current_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        # Calculate confidence based on sample size and consistency
        confidence = self._calculate_confidence(history)
        
        # Calculate improvement over baseline
        improvement = current_accuracy - baseline
        
        # Determine trend
        trend = self._calculate_trend(history)
        
        # Calculate additional metrics
        avg_resolution_time = np.mean([h["time_to_resolution"] for h in history if h["time_to_resolution"] > 0]) if history else 0
        
        return {
            "accuracy": current_accuracy,
            "confidence": confidence,
            "sample_size": total_predictions,
            "improvement": improvement,
            "improvement_percentage": improvement * 100,
            "trend": trend,
            "baseline_accuracy": baseline,
            "correct_predictions": correct_predictions,
            "avg_resolution_time": avg_resolution_time,
            "recent_performance": self._get_recent_performance(history)
        }
    
    def get_overall_metrics(self) -> Dict[str, Any]:
        """Get overall accuracy metrics across all incident types"""
        overall_metrics = {
            "total_feedback": 0,
            "overall_accuracy": 0,
            "overall_improvement": 0,
            "by_type": {}
        }
        
        accuracies = []
        improvements = []
        
        for incident_type in self.baseline_accuracy.keys():
            metrics = self.get_accuracy_metrics(incident_type)
            overall_metrics["by_type"][incident_type] = metrics
            overall_metrics["total_feedback"] += metrics["sample_size"]
            
            if metrics["sample_size"] > 0:
                accuracies.append(metrics["accuracy"])
                improvements.append(metrics["improvement"])
        
        if accuracies:
            overall_metrics["overall_accuracy"] = np.mean(accuracies)
            overall_metrics["overall_improvement"] = np.mean(improvements)
        
        return overall_metrics
    
    def _calculate_confidence(self, history: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on history"""
        if len(history) < 5:
            # Low confidence with small sample size
            return 0.3
        
        # Base confidence on sample size
        sample_confidence = min(0.9, len(history) / 50)
        
        # Adjust based on consistency
        if len(history) >= 10:
            recent = history[-10:]
            recent_accuracy = sum(1 for h in recent if h["correct"]) / 10
            consistency_factor = 1 - abs(recent_accuracy - 0.5) * 0.5
        else:
            consistency_factor = 0.7
        
        return sample_confidence * consistency_factor
    
    def _calculate_trend(self, history: List[Dict[str, Any]]) -> str:
        """Calculate accuracy trend"""
        if len(history) < 10:
            return "insufficient_data"
        
        # Compare recent vs older performance
        mid_point = len(history) // 2
        older = history[:mid_point]
        recent = history[mid_point:]
        
        older_accuracy = sum(1 for h in older if h["correct"]) / len(older)
        recent_accuracy = sum(1 for h in recent if h["correct"]) / len(recent)
        
        diff = recent_accuracy - older_accuracy
        
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"
    
    def _get_recent_performance(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get performance metrics for recent predictions"""
        if len(history) < 5:
            return {"sample_size": len(history), "accuracy": 0}
        
        recent = history[-10:]  # Last 10 predictions
        correct = sum(1 for h in recent if h["correct"])
        
        return {
            "sample_size": len(recent),
            "accuracy": correct / len(recent),
            "last_5_correct": sum(1 for h in history[-5:] if h["correct"])
        }
    
    def get_learning_curve(self, incident_type: str) -> List[Dict[str, Any]]:
        """Get learning curve data for visualization"""
        history = self.feedback_history.get(incident_type, [])
        
        if len(history) < 5:
            return []
        
        curve_data = []
        window_size = 5
        
        for i in range(window_size, len(history) + 1, 2):
            window = history[:i]
            accuracy = sum(1 for h in window if h["correct"]) / len(window)
            
            curve_data.append({
                "sample_count": i,
                "accuracy": accuracy,
                "timestamp": window[-1]["timestamp"]
            })
        
        return curve_data
    
    def get_common_mistakes(self, incident_type: str) -> List[Dict[str, Any]]:
        """Identify common prediction mistakes"""
        history = self.feedback_history.get(incident_type, [])
        
        mistakes = defaultdict(int)
        
        for h in history:
            if not h["correct"]:
                mistake_key = f"{h['predicted_cause']} -> {h['actual_cause']}"
                mistakes[mistake_key] += 1
        
        # Sort by frequency
        common_mistakes = []
        for mistake, count in sorted(mistakes.items(), key=lambda x: x[1], reverse=True)[:5]:
            predicted, actual = mistake.split(" -> ")
            common_mistakes.append({
                "predicted": predicted,
                "actual": actual,
                "frequency": count,
                "percentage": (count / len(history) * 100) if history else 0
            })
        
        return common_mistakes
    
    def simulate_feedback_improvement(self, incident_type: str, num_feedback: int = 50):
        """Simulate feedback to show improvement (for testing)"""
        # Start with baseline accuracy
        baseline = self.baseline_accuracy.get(incident_type, 0.5)
        
        # Simulate gradual improvement
        for i in range(num_feedback):
            # Accuracy improves logarithmically
            improvement_factor = np.log(i + 2) / np.log(num_feedback + 2)
            current_accuracy = baseline + (0.95 - baseline) * improvement_factor * 0.7
            
            # Add some randomness
            is_correct = np.random.random() < current_accuracy
            
            self.add_feedback_result({
                "incident_type": incident_type,
                "predicted_cause": f"Predicted_{i}",
                "actual_cause": f"Actual_{i}" if not is_correct else f"Predicted_{i}",
                "correct": is_correct,
                "confidence": current_accuracy,
                "time_to_resolution": np.random.randint(10, 120)
            })