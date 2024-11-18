import streamlit as st
import utils

# Ensure only admins can access this page
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("Bu sayfayı görüntülemek için lütfen giriş yapın.")
    st.stop()
elif st.session_state.role != 'admin':
    st.error("Bu sayfayı görüntülemek için yetkiniz yok.")
    st.stop()

# Page title
st.title("İş Takibi ve Görev Yönetimi - Adminler Arası İletişim")

# Sidebar for viewing task history
st.sidebar.subheader("Görev Geçmişi")
task_history = utils.get_task_history()  # Fetch past tasks from database

# Display task history in the sidebar
for task in task_history:
    st.sidebar.markdown(f"**ID:** {task['task_id']} - {task['title']}")
    st.sidebar.markdown(f"**Durum:** {task['status']} - Tamamlanma: {task['progress']}%")
    st.sidebar.markdown(f"**Tarih:** {task['created_at']}")
    st.sidebar.write("---")

# Task creation section
st.subheader("Yeni Görev Oluştur")

# Fetch admin usernames from utils
admin_usernames = utils.get_admin_usernames()

# Task creation form
with st.form("task_creation_form"):
    title = st.text_input("Görev Başlığı")
    description = st.text_area("Görev Açıklaması")
    assigned_to = st.multiselect("Görevi Atanan Adminler", options=admin_usernames)  # Use admin usernames for selection
    urgency = st.slider("Önem Derecesi", 1, 5)
    submit = st.form_submit_button("Görevi Oluştur")

    if submit:
        if title and description and assigned_to:
            # Create task in database
            task_id = utils.create_task(title, description, assigned_to, urgency)
            st.success(f"Yeni görev başarıyla oluşturuldu. Görev ID: {task_id}")
        else:
            st.error("Lütfen tüm alanları doldurun.")

# Task management section
st.subheader("Görev Listesi ve Durum Güncelleme")
tasks = utils.get_open_tasks()  # Retrieve all open tasks

# Display each task with status and action options
for task in tasks:
    st.markdown(f"### {task['title']} {'⭐' * task['urgency']}")
    st.write(task['description'])
    st.markdown(f"**Durum:** {'🔴 Görülmedi' if task['status'] == 'not seen' else '🟡 Süreç Başladı' if task['status'] == 'in progress' else '🟢 Tamamlandı'}")
    st.markdown(f"**Yaratıcı:** {task['created_by']} - **Atananlar:** {', '.join(task['assigned_to'].split(','))}")

    # Task update options for assigned admins
    if st.session_state.username in task['assigned_to']:
        if st.button("Gördüm", key=f"seen_{task['task_id']}"):
            utils.mark_task_as_seen(task['task_id'], st.session_state.username)
            st.rerun()

        if task['status'] == 'in progress':
            progress = st.slider("Görev İlerleme Durumu (%)", 0, 100, task['progress'], key=f"progress_{task['task_id']}")
            if st.button("İlerlemeyi Güncelle", key=f"update_progress_{task['task_id']}"):
                utils.update_task_progress(task['task_id'], progress)
                st.success("Görev ilerleme durumu güncellendi.")
                st.rerun()

        if st.button("İşi Kapat", key=f"complete_{task['task_id']}"):
            utils.complete_task(task['task_id'])
            st.rerun()

# Completed tasks section
st.subheader("Tamamlanmış Görevler")
completed_tasks = utils.get_completed_tasks()  # Retrieve completed tasks

# Display each completed task
for task in completed_tasks:
    st.markdown(f"**{task['title']}** - Tamamlanma Tarihi: {task['updated_at']}")
