# 1_admin.py

import streamlit as st
import utils  # Importing shared utility functions
import pandas as pd
from datetime import datetime
import os
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

# Initialize the database (already initialized in utils.py, but can be called here as well)
utils.init_db()

# Set up the title for the admin page
st.title("Admin Panel - QR Kod ve Varlık Yönetimi")

# ---------------------- User Authentication Check ----------------------
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("Bu sayfayı görüntülemek için lütfen giriş yapın.")
    st.stop()
else:
    if st.session_state.role != 'admin':
        st.error("Bu sayfayı görüntülemek için yetkiniz yok.")
        st.stop()

# ---------------------- Set up columns ----------------------
#col1, col2 = st.columns([1, 1])  # 3:1 ratio for left and right columns

#with col1:
# ---------------------- Sidebar: Display Asset History ----------------------
st.sidebar.subheader("Geçmiş")

history = utils.get_asset_history()

for record in history:
    varlik_id, varlik_adi, gönderen, alıcı, zaman = record
    st.sidebar.markdown(f"**ID:** {varlik_id}")
    st.sidebar.markdown(f"**Varlık Adı:** {varlik_adi}")
    st.sidebar.markdown(f"**Gönderen:** {gönderen}")
    st.sidebar.markdown(f"**Alıcı:** {alıcı}")
    st.sidebar.markdown(f"**Zaman Damgası:** {zaman}")
    if st.sidebar.button(f"Sil {varlik_id}", key=f"delete_{varlik_id}"):
        utils.delete_asset(varlik_id)
        st.success(f"{varlik_id} ID'li varlık başarıyla silindi.")
        # Send notification
        utils.send_pushbullet_notification(
            title="Varlık Silindi",
            message=f"Varlık ID: {varlik_id} silindi."
        )
        st.rerun()

# ---------------------- QR Code Creation Section ----------------------
st.subheader("QR Kod Oluşturma")

# Starting QR code creation process
if 'qr_creation_started' not in st.session_state:
    st.session_state.qr_creation_started = False

# Button to start QR code creation
if not st.session_state.qr_creation_started:
    if st.button("QR kod yaratmaya başla"):
        # Reset recent QR codes Excel file
        utils.create_empty_excel(utils.recent_qr_codes_file, ["id", "QR-codes-text", "QR-codes-images"])
        st.session_state.qr_creation_started = True
        st.success("QR kod yaratma işlemi başlatıldı ve recent_qr_codes12.xlsx dosyası sıfırlandı.")
else:
    # QR code creation form
    st.write("QR kod yaratma işlemi başlatıldı.")
    with st.form("qr_code_creation_form"):
        assetname = st.selectbox("Varlık Seç", ["QWE", "RTY", "UIO", "PAS"])
        unit = st.selectbox("Ölçü Birimini Seç", ["metre", "kg", "rulo"])
        miktar = st.number_input("Miktarı Girin", min_value=1, step=1)
        adet = st.number_input("Çarpan (adet)", min_value=1, step=1, value=1)
        gönderen = st.text_input("Gönderen")
        alıcı = st.text_input("Alıcı")
        submit = st.form_submit_button("QR Kod Oluştur")

    if submit:
        if not gönderen or not alıcı:
            st.error("Lütfen hem gönderen hem de alıcıyı belirtin.")
        else:
            qr_codes_info = utils.generate_qr_codes(assetname, unit, miktar, adet, gönderen, alıcı)
            st.success(f"{adet} QR kod başarıyla oluşturuldu!")

            # Display generated QR codes and IDs
            st.subheader("Oluşturulan QR Kodları ve ID'leri")
            for qr_info in qr_codes_info:
                st.image(qr_info['image_path'], width=150)
                st.write(f"ID: {qr_info['id']}")

            # Provide option to download QR codes Excel file
            excel_qr_codes_file = "qr_codes_output.xlsx"
            with open(excel_qr_codes_file, "rb") as f:
                excel_data = f.read()
                st.download_button(
                    label="QR Kodları Excel Olarak İndir",
                    data=excel_data,
                    file_name=excel_qr_codes_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    # Button to end QR code creation
    if st.button("QR kod yaratmayı bitir"):
        st.session_state.qr_creation_started = False
        st.success("QR kod yaratma işlemi tamamlandı ve recent_qr_codes12.xlsx dosyasına kaydedildi.")
        # Send notification to admins
        utils.send_pushbullet_notification(
            title="Admin Aksiyonu: QR Kod Yaratma Tamamlandı",
            message=f"QR kod yaratma işlemi {st.session_state.username} tarafından tamamlandı."
        )

# ---------------------- Asset Addition Section ----------------------
st.subheader("Varlık Ekle")
if st.button("Varlık Ekle"):
    utils.add_assets_from_recent_qr_codes()
    st.success("Varlıklar başarıyla eklendi ve veritabanına kaydedildi.")
    # Send notification to admins
    utils.send_pushbullet_notification(
        title="Admin Aksiyonu: Varlık Eklendi",
        message=f"Varlıklar {st.session_state.username} tarafından eklendi."
    )


# ---------------------- Display Assets in Storage ----------------------
st.subheader("Depodaki Mevcut Varlıklar")
assets_df = utils.get_current_stock_levels()  # Get the assets from the database

if not assets_df.empty:
    # Display assets in a table
    st.dataframe(assets_df)
else:
    st.write("Depoda şu anda hiç varlık yok.")

# ---------------------- Asset Filtering Section ----------------------
st.subheader("Varlıkları Filtrele")
filter_option = st.selectbox("Filtreleme Kriteri", ["Hepsi", "Varlık Adı", "Gönderen", "Alıcı"])
filter_query = st.text_input("Filtre Değerini Girin")

if st.button("Varlıkları Filtrele"):
    filtered_assets_df = utils.get_filtered_assets(filter_option, filter_query)
    if not filtered_assets_df.empty:
        st.dataframe(filtered_assets_df)

        # Add an export button for filtered assets
        st.download_button(
            label="Varlıkları Excel Olarak İndir",
            data=utils.convert_df_to_excel(filtered_assets_df),
            file_name='filtered_assets.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.write("Kriterlere uyan varlık bulunamadı.")

# ---------------------- Asset Movements Section ----------------------
st.subheader("Varlık Hareketleri")

movements_data = utils.get_asset_movements()

if not movements_data.empty:
    st.dataframe(movements_data)

    # Add a selectbox to choose a movement to undo
    movement_id_to_undo = st.number_input("Geri Alınacak Hareket ID'sini Girin", min_value=1, step=1)
    if st.button("Hareketi Geri Al"):
        success = utils.undo_asset_movement(movement_id_to_undo)
        if success:
            st.success("Hareket başarıyla geri alındı.")
            st.rerun()
        else:
            st.error("Hareket geri alınamadı.")
else:
    st.write("Henüz varlık hareketi yok.")

# ---------------------- Movement Filtering Section ----------------------
st.subheader("Varlık Hareketlerini Filtrele")
action_type = st.selectbox("Aksiyon Türü", ["Hepsi", "Kullanıldı", "İşlem İçin Gönderildi", "Geri Alındı"])
start_date = st.date_input("Başlangıç Tarihi")
end_date = st.date_input("Bitiş Tarihi")

if st.button("Hareketleri Filtrele"):
    filtered_movements_data = utils.get_filtered_movements(action_type, start_date, end_date)
    if not filtered_movements_data.empty:
        st.dataframe(filtered_movements_data)

        # Add an export button for filtered movements
        st.download_button(
            label="Hareketleri Excel Olarak İndir",
            data=utils.convert_df_to_excel(filtered_movements_data),
            file_name='filtered_movements.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.write("Kriterlere uyan hareket bulunamadı.")

# ---------------------- Additional Admin Features ----------------------
# You can add more features here, such as generating reports, viewing statistics, etc.

import time  # Import time for flush printing


