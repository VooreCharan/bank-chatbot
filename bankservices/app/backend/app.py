import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://fxkvotijpsssahfumgli.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4a3ZvdGlqcHNzc2FoZnVtZ2xpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2NjA0NjksImV4cCI6MjA2MDIzNjQ2OX0.PyDNf02l7ZHYkp0F7rPzg-Zn__AzNrS0Qen8S16GElg")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyB0t9beTgAThsc-E1hTKbAbmGNp5y9CN8Y")
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "412c998b3ddce3e2989fd8779caece76e58378d6")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Gemini Embeddings
try:
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GEMINI_API_KEY
    )
    print("Gemini embeddings initialized successfully.")
except Exception as e:
    print(f"Error initializing Gemini embeddings: {e}")
    embeddings = None

class BankingMemory:
    def __init__(self, user_id):
        self.user_id = user_id
    
    def store_memory(self, question: str, answer: str):
        if embeddings is None:
            data = {
                "user_id": self.user_id,
                "question": question,
                "answer": answer,
                "embedding": None,
                "timestamp": datetime.now().isoformat()
            }
        else:
            try:
                question_embedding = embeddings.embed_query(question)
                data = {
                    "user_id": self.user_id,
                    "question": question,
                    "answer": answer,
                    "embedding": question_embedding,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                print(f"Embedding error: {e}")
                data = {
                    "user_id": self.user_id,
                    "question": question,
                    "answer": answer,
                    "embedding": None,
                    "timestamp": datetime.now().isoformat()
                }
        
        response = supabase.table("banking_memory").insert(data).execute()
        return response
    
    def retrieve_relevant_memories(self, question: str, limit: int = 3):
        if embeddings is None:
            response = supabase.table("banking_memory").select("*").eq("user_id", self.user_id).eq("question", question).limit(limit).execute()
            return response.data
        
        try:
            question_embedding = embeddings.embed_query(question)
            response = supabase.rpc(
                "match_memories",
                {
                    "query_embedding": question_embedding,
                    "match_threshold": 0.8,
                    "match_count": limit,
                    "user_id_filter": self.user_id
                }
            ).execute()
            return response.data
        except Exception as e:
            print(f"Memory retrieval error: {e}")
            return []

class BankDataRetriever:
    def __init__(self):
        self.serper_api_key = SERPER_API_KEY
        self.bank_domain = "chase.com"
    
    def search_bank_info(self, query: str):
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json"
        }
        params = {
            "q": f"site:{self.bank_domain} {query}",
            "num": 3
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            results = response.json()
            return self._extract_relevant_info(results)
        except requests.RequestException as e:
            return f"Unable to fetch real-time data: {str(e)}"
    
    def _extract_relevant_info(self, results):
        if "organic" in results:
            return "\n".join([result.get("snippet", "") for result in results["organic"] if result.get("snippet")])
        return "No relevant information found."

class BankingChatbot:
    def __init__(self, user_id):
        self.user_id = user_id
        self.memory = BankingMemory(user_id)
        self.data_retriever = BankDataRetriever()
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""
            You are a helpful banking assistant for Chase Bank. Use the following context from previous conversations and real-time data to answer the user's question accurately.
            
            Context: {context}
            
            Question: {question}
            
            Answer:
            """
        )
    
    def process_query(self, question: str):
        # Retrieve relevant memories
        memories = self.memory.retrieve_relevant_memories(question)
        memory_context = "\n".join([f"Previous Q: {m['question']} - A: {m['answer']}" for m in memories]) if memories else ""
        
        # Check if the question references previous conversations
        if any(phrase in question.lower() for phrase in ["as discussed", "as explained", "last conversation", "previously"]):
            conversation_context = memory_context or "I don't have record of our previous conversation about this. I'll provide fresh information."
        else:
            conversation_context = memory_context
        
        # Get real-time data for certain types of questions
        real_time_data = ""
        keywords = ["fees", "policy", "process", "rates", "balance", "account", "loan", "credit", "debit", "transfer"]
        if any(keyword in question.lower() for keyword in keywords):
            real_time_data = self.data_retriever.search_bank_info(question)
            real_time_context = f"Real-time data: {real_time_data}"
        else:
            real_time_context = ""
        
        context = "\n".join(filter(None, [conversation_context, real_time_context])).strip()
        
        # Generate response
        answer = self._generate_response(context, question)
        
        # Store the interaction in memory
        self.memory.store_memory(question, answer)
        
        return {
            "answer": answer,
            "context": context if context else "general knowledge",
            "has_memory": bool(memories)
        }
    
    def _generate_response(self, context, question):
        # Expanded responses for better user experience
        if "fees" in question.lower():
            return "Chase Bank typically charges a 3% fee for international transactions. This applies to all debit and credit card purchases made in foreign currencies. There's also a $5 fee for international ATM withdrawals, plus any fees the ATM owner may charge. For wire transfers, domestic incoming transfers are $15, domestic outgoing are $25-35, and international wire transfers range from $40-50 depending on your account type."
        
        elif "account balance" in question.lower():
            return "You can check your Chase account balance through several methods: 1) Log into Chase Mobile app, 2) Visit chase.com and log into your account, 3) Call the automated service at 1-800-935-9935, 4) Check at any Chase ATM with your debit card, or 5) Visit a local Chase branch with identification. The mobile app and website also provide additional account details like pending transactions and scheduled payments."
        
        elif "loan interest rates" in question.lower():
            return "Chase offers competitive interest rates that vary based on loan type, credit score, loan amount, and term length. Currently, auto loans start around 4.5% APR, mortgages around 6.5% APR for 30-year fixed rates, and personal loans from 7.49% APR. For the most current and personalized rates, I recommend visiting chase.com/loans or speaking with a Chase loan officer who can provide rates specific to your financial situation."
        
        elif "password" in question.lower():
            return "To reset your Chase online banking password: 1) Go to chase.com or open the Chase Mobile app, 2) Click 'Forgot username/password', 3) Enter your username, 4) Verify your identity through a code sent to your phone or email, 5) Create a new password following the security requirements, 6) Log in with your new password. For security reasons, your password should be unique, include a mix of characters, and not be used for other accounts."
        
        elif "open" in question.lower() and "account" in question.lower():
            return "To open a new Chase account: 1) Gather your ID (driver's license or passport), Social Security number, and address information, 2) Choose between applying online at chase.com/checking, through the Chase Mobile app, or visiting a branch in person, 3) Select the account type that best suits your needs, 4) Complete the application form, 5) Fund your new account (minimum deposits vary by account type), 6) Set up online banking access. The process typically takes 10-15 minutes online or about 30 minutes in a branch."
        
        elif "credit card rewards" in question.lower():
            return "Chase credit cards offer a variety of rewards programs including cash back, travel points, and bonus categories. You can redeem points for travel, gift cards, or statement credits. For detailed information, visit chase.com/rewards or check your specific card's terms and conditions."
        
        elif "branch location" in question.lower() or "branch hours" in question.lower():
            return "You can find Chase branch locations and their hours by visiting chase.com/locator. Most branches are open Monday through Friday from 9 AM to 5 PM, with some branches offering weekend hours."
        
        elif "atm fee" in question.lower() or "atm location" in question.lower():
            return "Chase does not charge fees for using Chase ATMs. For non-Chase ATMs, fees may apply. You can find nearby Chase ATMs using the Chase Mobile app or at chase.com/locator."
        
        elif "dispute" in question.lower() or "transaction issue" in question.lower():
            return "To dispute a transaction, log into your Chase account online or via the mobile app, select the transaction, and follow the prompts to report an issue. You can also call Chase customer service at 1-800-935-9935 for assistance."
        
        elif "mobile app" in question.lower() and ("issue" in question.lower() or "problem" in question.lower()):
            return "If you are experiencing issues with the Chase Mobile app, try updating to the latest version, restarting your device, or reinstalling the app. For persistent problems, contact Chase support or visit chase.com/mobilehelp."
        
        elif "security" in question.lower() and ("tips" in question.lower() or "advice" in question.lower()):
            return "For online banking security, use strong unique passwords, enable two-factor authentication, avoid public Wi-Fi for banking, and regularly monitor your account for suspicious activity. Chase also offers alerts and fraud protection services."
        
        elif "wire transfer" in question.lower():
            return "Wire transfers can be done online, via phone, or at a branch. Domestic wire transfers typically cost $15-$35, and international wires range from $40-$50. Ensure you have the recipient's correct details to avoid delays."
        
        elif "check deposit" in question.lower():
            return "You can deposit checks using the Chase Mobile app by taking photos of the front and back of the check. Alternatively, visit a branch or ATM to deposit checks in person."
        
        elif "close account" in question.lower():
            return "To close your Chase account, ensure all pending transactions have cleared, withdraw remaining funds, and contact Chase customer service at 1-800-935-9935 or visit a branch to complete the closure process."
        
        # New queries added below
        elif "transaction history" in question.lower() or "recent transactions" in question.lower():
            return "You can view your recent transactions by logging into the Chase Mobile app or online banking at chase.com. Transactions are updated in real-time and include details such as date, amount, merchant, and transaction type."
        
        elif "account details" in question.lower() or "account information" in question.lower():
            return "Your Chase account details, including account number, type, and status, can be accessed securely through the Chase Mobile app or online banking portal. For privacy and security, this information is not shared over chat."
        
        elif "banking policies" in question.lower() or "terms and conditions" in question.lower():
            return "Chase banking policies and terms and conditions are available on the official website at chase.com/policies. These documents cover account usage, fees, privacy, and security policies."
        
        elif "account management" in question.lower() or "manage my account" in question.lower():
            return "You can manage your Chase account settings, update personal information, set up alerts, and more through the Chase Mobile app or online banking. For assistance, contact Chase customer service or visit a branch."
        
        elif "fund transfer" in question.lower() or "transfer funds" in question.lower():
            return "To transfer funds between your Chase accounts or to external accounts, use the Chase Mobile app or online banking. Transfers are typically instant between Chase accounts and may take 1-3 business days for external accounts."
        
        elif "statement" in question.lower() or "account statement" in question.lower():
            return "Monthly account statements are available online through your Chase account. You can view, download, or print statements for your records."
        
        elif "overdraft" in question.lower():
            return "Chase offers overdraft protection options to help you avoid declined transactions and fees. You can link a savings account or line of credit for overdraft coverage. For details, visit chase.com/overdraft."
        
        return "Based on the information available, I don't have a specific answer for your question. For the most accurate and up-to-date information, I recommend visiting chase.com, using the Chase Mobile app, or contacting Chase customer support at 1-800-935-9935. Chase representatives are available 24/7 to assist with your banking needs."

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id', 'anonymous')
    question = data.get('message')
    
    if not question:
        return jsonify({"error": "No message provided"}), 400
    
    chatbot = BankingChatbot(user_id)
    response = chatbot.process_query(question)
    
    return jsonify(response)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Banking Chatbot API is running"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)