import json
import time
import os
import sys
from typing import List, Dict, Any
import pytest


sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from helpdesk.core.system import HelpDeskSystem
from helpdesk.models.models import HelpDeskRequest, TestRequest

class TestHelpDeskSystem:
    """Test suite for the help desk system"""
    
    def __init__(self):
        self.help_desk = HelpDeskSystem()
        self.test_requests = self._load_test_requests()
    
    def _load_test_requests(self) -> List[TestRequest]:
        """Load test requests from JSON file"""
        try:
            with open("test_requests.json", 'r') as f:
                data = json.load(f)
                return [TestRequest(**req) for req in data['test_requests']]
        except FileNotFoundError:
            print("Warning: test_requests.json not found")
            return []
    
    def run_classification_tests(self) -> Dict[str, Any]:
        """Test classification accuracy"""
        print("Running classification tests...")
        
        results = {
            "total_tests": len(self.test_requests),
            "correct_classifications": 0,
            "classification_details": [],
            "accuracy": 0.0
        }
        
        for test_req in self.test_requests:
            # Create help desk request
            request = HelpDeskRequest(
                id=test_req.id,
                request=test_req.request
            )
            
            # Process request
            response = self.help_desk.process_request(request)
            
            # Check classification
            predicted_category = response.classification.category.value
            expected_category = test_req.expected_classification
            is_correct = predicted_category == expected_category
            
            if is_correct:
                results["correct_classifications"] += 1
            
            # Check escalation
            escalation_correct = response.escalation.should_escalate == test_req.escalate
            
            results["classification_details"].append({
                "request_id": test_req.id,
                "request": test_req.request,
                "expected_category": expected_category,
                "predicted_category": predicted_category,
                "classification_correct": is_correct,
                "confidence": response.classification.confidence,
                "expected_escalation": test_req.escalate,
                "predicted_escalation": response.escalation.should_escalate,
                "escalation_correct": escalation_correct,
                "processing_time": response.processing_time
            })
        
        results["accuracy"] = results["correct_classifications"] / results["total_tests"] if results["total_tests"] > 0 else 0
        
        return results
    
    def run_retrieval_tests(self) -> Dict[str, Any]:
        """Test knowledge retrieval quality"""
        print("Running retrieval tests...")
        
        results = {
            "total_tests": len(self.test_requests),
            "retrieval_details": [],
            "average_relevance": 0.0,
            "coverage_score": 0.0
        }
        
        total_relevance = 0.0
        total_coverage = 0.0
        
        for test_req in self.test_requests:
            # Get retrieved knowledge
            retrieved = self.help_desk.knowledge_retriever.retrieve(test_req.request)
            
            # Calculate average relevance score
            avg_relevance = sum(r.relevance_score for r in retrieved) / len(retrieved) if retrieved else 0.0
            total_relevance += avg_relevance
            
            # Check coverage of expected elements
            retrieved_text = " ".join([r.content.lower() for r in retrieved])
            covered_elements = sum(1 for element in test_req.expected_elements 
                                 if element.lower() in retrieved_text)
            coverage = covered_elements / len(test_req.expected_elements) if test_req.expected_elements else 0.0
            total_coverage += coverage
            
            results["retrieval_details"].append({
                "request_id": test_req.id,
                "request": test_req.request,
                "expected_elements": test_req.expected_elements,
                "retrieved_count": len(retrieved),
                "average_relevance": avg_relevance,
                "coverage_score": coverage,
                "retrieved_sources": [r.source for r in retrieved]
            })
        
        results["average_relevance"] = total_relevance / results["total_tests"] if results["total_tests"] > 0 else 0
        results["coverage_score"] = total_coverage / results["total_tests"] if results["total_tests"] > 0 else 0
        
        return results
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Test system performance"""
        print("Running performance tests...")
        
        processing_times = []
        
        # Run multiple iterations for performance measurement
        for _ in range(3):
            for test_req in self.test_requests:
                request = HelpDeskRequest(request=test_req.request)
                start_time = time.time()
                response = self.help_desk.process_request(request)
                end_time = time.time()
                
                processing_times.append(end_time - start_time)
        
        return {
            "total_requests_processed": len(processing_times),
            "average_processing_time": sum(processing_times) / len(processing_times),
            "min_processing_time": min(processing_times),
            "max_processing_time": max(processing_times),
            "requests_per_second": len(processing_times) / sum(processing_times) if sum(processing_times) > 0 else 0
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        print("Starting comprehensive test suite...")
        
        start_time = time.time()
        
        results = {
            "test_summary": {
                "total_test_requests": len(self.test_requests),
                "test_start_time": start_time
            },
            "classification_tests": self.run_classification_tests(),
            "retrieval_tests": self.run_retrieval_tests(),
            "performance_tests": self.run_performance_tests()
        }
        
        end_time = time.time()
        results["test_summary"]["total_test_time"] = end_time - start_time
        results["test_summary"]["test_end_time"] = end_time
        
        return results
    
    def print_test_summary(self, results: Dict[str, Any]):
        """Print a formatted test summary"""
        print("\n" + "="*60)
        print("HELP DESK SYSTEM TEST RESULTS")
        print("="*60)
        
        # Classification results
        classification = results["classification_tests"]
        print(f"\nCLASSIFICATION ACCURACY: {classification['accuracy']:.2%}")
        print(f"Correct: {classification['correct_classifications']}/{classification['total_tests']}")
        
        # Retrieval results
        retrieval = results["retrieval_tests"]
        print(f"\nRETRIEVAL QUALITY:")
        print(f"Average Relevance Score: {retrieval['average_relevance']:.3f}")
        print(f"Expected Element Coverage: {retrieval['coverage_score']:.2%}")
        
        # Performance results
        performance = results["performance_tests"]
        print(f"\nPERFORMANCE METRICS:")
        print(f"Average Processing Time: {performance['average_processing_time']:.3f}s")
        print(f"Requests per Second: {performance['requests_per_second']:.1f}")
        
        print(f"\nTotal Test Time: {results['test_summary']['total_test_time']:.2f}s")
        print("="*60)

def main():
    """Run the test suite"""
    try:
        tester = TestHelpDeskSystem()
        results = tester.run_all_tests()
        tester.print_test_summary(results)
        
        # Save detailed results
        with open("test_results.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print("\nDetailed results saved to test_results.json")
        
    except Exception as e:
        print(f"Error running tests: {e}")

if __name__ == "__main__":
    main()
