import streamlit as st
import requests
import json
import base64
from PIL import Image
import io

st.set_page_config(page_title="AI Platform", layout="wide")

def main():
    st.title("AI Platform")
    
    tab1, tab2, tab3 = st.tabs(["RAG System", "Plant Classification", "Marketplace"])
    
    with tab1:
        st.header("Document Q&A System")
        
        # Document upload
        uploaded_file = st.file_uploader("Upload a document", key="doc_upload")
        if uploaded_file:
            content = uploaded_file.read().decode()
            response = requests.post(
                "http://localhost:8000/add_document",
                json={"text": content}
            )
            if response.status_code == 200:
                st.success("Document uploaded successfully!")
        
        # Question asking
        question = st.text_input("Ask a question about your documents")
        if question:
            response = requests.post(
                "http://localhost:8000/query",
                json={"question": question}
            )
            if response.status_code == 200:
                data = response.json()
                st.write("Answer:", data["answer"])
                with st.expander("View source documents"):
                    for doc in data["source_documents"]:
                        st.write(doc)
    
    with tab2:
        st.header("Plant Disease Classification")
        
        uploaded_file = st.file_uploader("Upload a plant image", type=["jpg", "png", "jpeg"], key="img_upload")
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            if st.button("Classify"):
                files = {"file": uploaded_file.getvalue()}
                response = requests.post("http://localhost:8001/classify", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("English Classification:", result["english_classification"])
                        st.write("Confidence:", f"{result['confidence']:.2%}")
                    
                    with col2:
                        st.write("Urdu Translation:", result["urdu_translation"])
                        
                        # Play audio button
                        audio_bytes = base64.b64decode(result["audio_base64"])
                        st.audio(audio_bytes, format="audio/mp3")
    
    with tab3:
        st.header("Marketplace")
        
        # Get products
        response = requests.get("http://localhost:8002/products/")
        if response.status_code == 200:
            products = response.json()
            
            # Display products in a grid
            cols = st.columns(3)
            for idx, product in enumerate(products):
                with cols[idx % 3]:
                    st.image(product["image_url"], use_column_width=True)
                    st.write(f"**{product['name']}**")
                    st.write(product["description"])
                    st.write(f"Price: ${product['price']:.2f}")
                    
                    if st.button(f"Buy Now", key=f"buy_{product['id']}"):
                        checkout_response = requests.post(
                            f"http://localhost:8002/create-checkout-session/{product['id']}"
                        )
                        if checkout_response.status_code == 200:
                            checkout_url = checkout_response.json()["checkout_url"]
                            st.markdown(f"[Click here to complete your purchase]({checkout_url})")

if __name__ == "__main__":
    main()