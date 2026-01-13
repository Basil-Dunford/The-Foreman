from backend.risk_scouter import analyze_risk
import logging
import sys

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

def test_risk():
    print("Testing Risk Analysis...")
    description = "We are building a Manufacturing industrial facility in an area that receives more vibration than usual"
    
    try:
        result = analyze_risk(description)
        print("\nAnalysis Result:")
        print(result["analysis"][:200] + "...")
        print("\nRelevant Projects:", result["relevant_past_projects"])
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_risk()
