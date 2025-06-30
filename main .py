# main.py

from tutor_engine import TutorEngine

def main():
    """
    Initializes the TutorEngine and runs the main interactive chat loop.
    """
    # This one line sets up everything!
    tutor = TutorEngine()
     
    print("\n--- Welcome to the Learning Tutor Bot ---")
    print("You can ask any question about your course material.")
    print("Type 'quit' or 'exit' to end the session.")
    print("-" * 40)

    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ["quit", "exit"]:
            print("Tutor: Goodbye! Keep up the great work.")
            break
        
        if not user_input.strip():
            continue
            
        # The TutorEngine class handles all the complex logic.
        tutor_guiding_question = tutor.get_guidance(user_input)
        
        print(f"\nTutor: {tutor_guiding_question}\n")

if __name__ == "__main__":
    main()