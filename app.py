import streamlit as st
from PIL import Image, ImageGrab
import numpy as np
import easyocr
import pinyin
from collections import defaultdict
from googletrans import Translator
import asyncio


class ImgToPinyin:
    def __init__(self):
        self.reader = easyocr.Reader(['ch_sim', 'en'])
        self.lines = defaultdict(list)
        self.translator = Translator()

    async def ocr(self, img):
        # Convert PIL image to numpy array
        img_array = np.array(img)

        text = ""
        pinyin_text = ""
        self.lines.clear()
        result = self.reader.readtext(img_array)

        for box, text, conf in result:
            y_center = (box[0][1] + box[2][1]) / 2
            self.lines[round(y_center, -1)].append((box, text, conf))

        sorted_lines = sorted(self.lines.items())
        for _, content in sorted_lines:
            content.sort(key=lambda x: x[0][0][0])
            res = " ".join(item[1] for item in content)
            text += res + "\n"
            pinyin_text += pinyin.get(res, delimiter="") + "\n"
        return text.strip(), pinyin_text.strip()

    async def translate(self, text, target_language):
        if not text.strip():
            return "No text to translate."
        try:
            translated = await self.translator.translate(text, dest=target_language)
            return translated.text
        except Exception as e:
            return f"Error during translation: {e}"


def main():
    st.title("Image to Pinyin Translator")
    st.sidebar.header("Options")
    mode = st.sidebar.radio("Select mode", ["Paste", "Upload"])

    img_to_pinyin = ImgToPinyin()

    # Initialize session state for text, Pinyin, and translations
    if "text" not in st.session_state:
        st.session_state.text = ""
    if "pinyin_text" not in st.session_state:
        st.session_state.pinyin_text = ""
    if "translation" not in st.session_state:
        st.session_state.translation = ""

    uploaded_image = None
    if mode == "Upload":
        uploaded_image = st.file_uploader("Upload an image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
    elif mode == "Paste":
        if st.button("Paste Image from Clipboard"):
            try:
                uploaded_image = ImageGrab.grabclipboard()  # Get image from clipboard
                if not isinstance(uploaded_image, Image.Image):
                    st.error("No image found in clipboard. Please copy an image and try again.")
                    return
            except Exception as e:
                st.error(f"Error accessing clipboard: {e}")
                return

    if uploaded_image is not None:
        with st.spinner("Processing image..."):
            text, pinyin_text = asyncio.run(img_to_pinyin.ocr(uploaded_image))
            st.session_state.text = text
            st.session_state.pinyin_text = pinyin_text

    st.subheader("Extracted Text")
    st.text(st.session_state.text)

    st.subheader("Pinyin")
    st.text(st.session_state.pinyin_text)

    # Translation buttons
    if st.session_state.text.strip():
        if st.button("Translate to English"):
            with st.spinner("Translating to English..."):
                translation = asyncio.run(img_to_pinyin.translate(st.session_state.text, target_language="en"))
                st.session_state.translation = translation

        if st.button("Translate to Vietnamese"):
            with st.spinner("Translating to Vietnamese..."):
                translation = asyncio.run(img_to_pinyin.translate(st.session_state.text, target_language="vi"))
                st.session_state.translation = translation

    if st.session_state.translation:
        st.subheader("Translation")
        st.text(st.session_state.translation)


if __name__ == "__main__":
    main()
