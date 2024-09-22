import google.generativeai as genai

# Set up your API key
genai.configure(api_key='AIzaSyAGEUXg33hKqTo7KbfW9P7Udrbz1I9ZJ4c')
model = genai.GenerativeModel("gemini-1.5-flash-latest")
print(model.model_name)
response = model.generate_content("Write a story about a magic backpack.")
#print(response.text)