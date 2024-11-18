# main.py
# open_ai_api_key = "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"
import streamlit as st
import utils  # Importing utility functions for common tasks

# The database and necessary files are initialized in utils.py when it's imported.

# Set up the main page
st.title("Depo Takip Sistemi")

st.write("""
Hoş geldiniz! Bu uygulama, depo yönetimini kolaylaştırmak ve varlıkları etkili bir şekilde takip etmek için tasarlanmıştır.

Lütfen sol taraftaki menüyü kullanarak istediğiniz sayfaya gidin:

- **Admin Paneli:** QR kodları oluşturabilir, varlıkları yönetebilir ve raporları görüntüleyebilirsiniz.
- **Çalışan Paneli:** QR kodlarını tarayarak varlıkları kullanabilir veya işlem için gönderebilirsiniz.
""")

# Note: The admin and worker functionalities are located in `pages/1_admin.py` and `pages/2_worker.py`.
# Run this app using `streamlit run main.py` and access the pages through the sidebar.

# You can add additional content or features below if needed.

# Optional: Role Selection (Uncomment if you want to use it)
# st.subheader("Lütfen Rolünüzü Seçin")
# role = st.selectbox("Rol Seçin", ["Admin", "Çalışan"])

# if role == "Admin":
#     st.write("Sol taraftaki menüden Admin Paneline erişebilirsiniz.")
# elif role == "Çalışan":
#     st.write("Sol taraftaki menüden Çalışan Paneline erişebilirsiniz.")

# Since Streamlit's multipage app feature automatically creates sidebar navigation based on the 'pages' directory,
# users can navigate to different pages directly from the sidebar.

# main.py

import streamlit as st
import utils

st.title("Depo Takip Sistemi")

# User Authentication
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.sidebar.subheader("Giriş Yap")
    username = st.sidebar.text_input("Kullanıcı Adı")
    password = st.sidebar.text_input("Şifre", type="password")
    if st.sidebar.button("Giriş"):
        role = utils.authenticate_user(username, password)
        if role:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = role
            st.sidebar.success(f"Hoş geldiniz, {username}!")
            st.rerun()
        else:
            st.sidebar.error("Geçersiz kullanıcı adı veya şifre.")
else:
    st.sidebar.write(f"Hoş geldiniz, {st.session_state.username}!")
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.logged_in = False
        st.session_state.username = ''
        st.session_state.role = ''
        st.rerun()
