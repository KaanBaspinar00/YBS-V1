# 2_worker.py

import streamlit as st
import utils  # Importing shared utility functions
from pyzbar.pyzbar import decode
from PIL import Image
from datetime import datetime

# User Authentication Check
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("Bu sayfayı görüntülemek için lütfen giriş yapın.")
    st.stop()
else:
    if st.session_state.role not in ['admin', 'worker']:
        st.error("Bu sayfayı görüntülemek için yetkiniz yok.")
        st.stop()

# Set up the title for the worker page
st.title("Çalışan Paneli - Varlık Tarama ve İşlemleri")

# ---------------------- Function to Display Asset Details ----------------------

def display_asset_details(asset):
    """Display asset details and provide options to perform actions."""
    entry_id, id_, qr_kodu, varlık_adı, gönderen, alıcı, miktar, unit, \
    adet, kacıncı, zaman, quantity = asset

    st.write(f"**ID:** {id_}")
    st.write(f"**Varlık Adı:** {varlık_adı}")
    st.write(f"**Gönderen:** {gönderen}")
    st.write(f"**Alıcı:** {alıcı}")
    st.write(f"**Miktar:** {miktar} {unit}")
    st.write(f"**Adet (Çarpan):** {adet}")
    st.write(f"**Kaçıncı:** {kacıncı}")
    st.write(f"**Zaman:** {zaman}")
    st.write(f"**Mevcut Stok:** {quantity}")

    # Provide action options
    st.subheader("Aksiyon Seçin")
    action = st.selectbox(
        "Aksiyon",
        ["Seçiniz", "Kullan", "İşlem İçin Gönder", "İşlemden Gelen Malı Geri Al"]
    )

    if action != "Seçiniz":
        quantity_input = st.number_input(
            "Miktar",
            min_value=1,
            max_value=quantity if action != "İşlemden Gelen Malı Geri Al" else None,
            value=1
        )
        partner_firm = ""
        notes = st.text_area("Notlar")

        if action == "İşlem İçin Gönder":
            partner_firm = st.text_input("Firma Adı")
        elif action == "İşlemden Gelen Malı Geri Al":
            partner_firm = st.text_input("Gönderen Firma Adı")

        # Move "Çalışan Adı" input here
        worker_name = st.text_input("Çalışan Adı")

        # Place the button after all inputs
        if st.button("Aksiyonu Kaydet"):
            if not worker_name:
                st.error("Lütfen çalışan adını girin.")
            else:
                action_code = ""
                if action == "Kullan":
                    action_code = "used"
                elif action == "İşlem İçin Gönder":
                    action_code = "sent_for_processing"
                elif action == "İşlemden Gelen Malı Geri Al":
                    action_code = "received_back"
                else:
                    st.error("Lütfen geçerli bir aksiyon seçin.")

                if action_code:
                    if action_code == "sent_for_processing" and not partner_firm:
                        st.error("Lütfen firma adını girin.")
                    else:
                        utils.log_asset_movement(
                            id_, action_code, quantity_input,
                            partner_firm, worker_name, notes
                        )
                        st.success("Aksiyon başarıyla kaydedildi.")
                        # Refresh the asset details to show updated quantity
                        st.rerun()

# ---------------------- QR Code Scanning Section ----------------------

st.subheader("QR Kodunu Tara")
image = st.camera_input("QR kodunun fotoğrafını çekin veya yükleyin")

if image:
    try:
        # Decode the QR code
        qr_image = Image.open(image)
        decoded_info = decode(qr_image)

        if decoded_info:
            qr_code_data = decoded_info[0].data.decode('utf-8')
            st.write(f"**Tarandı:** {qr_code_data}")

            # Fetch asset information from the database using the full QR code data
            asset = utils.get_asset_by_qr(qr_code_data)

            if asset:
                # Display asset details and actions
                display_asset_details(asset)
            else:
                st.error("Varlık veritabanında bulunamadı.")
        else:
            st.error("QR kodu algılanamadı. Lütfen tekrar deneyin.")
    except Exception as e:
        st.error(f"Resim işlenirken bir hata oluştu: {e}")

# ---------------------- Search for Assets ----------------------

st.subheader("Varlık Ara")
search_option = st.selectbox("Arama Kriteri", ["ID", "Varlık Adı"])
search_query = st.text_input("Arama Değerini Girin")

if st.button("Varlık Ara"):
    if search_query:
        if search_option == "ID":
            asset = utils.get_asset_by_id(search_query)
        elif search_option == "Varlık Adı":
            asset = utils.get_asset_by_name(search_query)
        else:
            asset = None

        if asset:
            display_asset_details(asset)
        else:
            st.error("Varlık bulunamadı.")
    else:
        st.error("Lütfen arama değerini girin.")

# ---------------------- View Asset Movement History ----------------------

st.subheader("Varlık Geçmişini Görüntüle")
asset_id_for_history = st.text_input("Varlık ID'sini Girin", key="history_asset_id")

if st.button("Geçmişi Göster"):
    if asset_id_for_history:
        history_data = utils.get_asset_history_by_id(asset_id_for_history)
        if not history_data.empty:
            st.dataframe(history_data)
        else:
            st.write("Bu varlık için hareket bulunamadı.")
    else:
        st.error("Lütfen Varlık ID'sini girin.")

# ---------------------- Display Recent Asset Movements ----------------------

st.subheader("Son Varlık Hareketleri")
movements_data = utils.get_asset_movements()

if not movements_data.empty:
    # Display recent asset movements
    st.dataframe(movements_data.head(10))
else:
    st.write("Henüz varlık hareketi yok.")

# ---------------------- Additional Worker Features ----------------------
# You can add more features here, such as notifications, task assignments, etc.
# ---------------------- Undo Last Action ----------------------

st.subheader("Son Aksiyonu Geri Al")

worker_name_for_undo = st.text_input("Çalışan Adı (Geri Alma İçin)", key="undo_worker_name")
if st.button("Son Aksiyonu Geri Al"):
    if not worker_name_for_undo:
        st.error("Lütfen çalışan adınızı girin.")
    else:
        last_movement = utils.get_last_movement_by_worker(worker_name_for_undo)
        if last_movement:
            movement_id, asset_id, action, quantity = last_movement
            success = utils.undo_asset_movement(movement_id)
            if success:
                st.success("Son aksiyon başarıyla geri alındı.")
            else:
                st.error("Aksiyon geri alınamadı.")
        else:
            st.error("Geri alınacak aksiyon bulunamadı.")
