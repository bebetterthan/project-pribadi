"""
Test available Gemini models
"""
import google.generativeai as genai
import sys

def list_available_models(api_key: str):
    try:
        print("🔍 Checking available Gemini models...")
        genai.configure(api_key=api_key)

        models = genai.list_models()

        print("\n✅ Available models:\n")
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f"  • {model.name}")
                print(f"    Display Name: {model.display_name}")
                print(f"    Description: {model.description[:100]}...")
                print()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        list_available_models(sys.argv[1])
    else:
        print("Usage: python test_models.py YOUR_API_KEY")
