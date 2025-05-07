import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Cloud To-Do List", layout="wide")
st.title("☁️ My Cloud To-Do List")
st.caption("Powered by AWS Chalice & Streamlit")


# --- Configuration ---
# User's actual deployed API endpoint that should preferably end with /tasks,
# or be the base /api path (the code below will try to append /tasks if it's not there).
USER_DEPLOYED_API_URL_DEFAULT = (
    "https://tio2f44dq1.execute-api.us-east-1.amazonaws.com/api/tasks"  # Your default
)

# This variable will hold the string value from the text_input
chalice_api_url_from_user = st.text_input(
    "Enter your Chalice API URL (base path or specific /tasks endpoint):",  # Corrected Label
    USER_DEPLOYED_API_URL_DEFAULT,  # User's default
)

# TASK_ENDPOINT will be the URL used for requests, ensuring it points to the /tasks resource.
TASK_ENDPOINT = ""  # Initialize
if chalice_api_url_from_user:
    # Normalize by removing trailing slash before checking/appending
    base_url_for_logic = chalice_api_url_from_user.strip("/")
    if base_url_for_logic.endswith("/tasks"):
        TASK_ENDPOINT = base_url_for_logic
    else:
        TASK_ENDPOINT = base_url_for_logic + "/tasks"
else:
    # This state will be caught by is_api_configured()
    pass


# --- Helper Functions to Interact with Backend ---
def is_api_configured():
    """Checks if the API endpoint seems minimally configured."""
    if (
        not TASK_ENDPOINT or "execute-api" not in TASK_ENDPOINT
    ):  # Basic check for AWS API Gateway URL
        st.sidebar.warning(
            "Please enter a valid Chalice API URL above to enable app functionality."
        )
        return False
    return True


def get_all_tasks():
    if not is_api_configured():
        return []
    try:
        response = requests.get(TASK_ENDPOINT)
        response.raise_for_status()
        # Assuming Chalice returns {'tasks': [...]}
        return response.json().get("tasks", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching tasks: {e}")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching tasks: {e}")
        return []


def add_new_task(title, due_date):
    if not is_api_configured():
        return None
    payload = {"title": title, "dueDate": due_date}
    try:
        response = requests.post(TASK_ENDPOINT, json=payload)
        response.raise_for_status()
        added_task_data = response.json().get("task", {})
        added_title = added_task_data.get("title", title)
        st.success(f"Task '{added_title}' added successfully!")
        return added_task_data
    except requests.exceptions.RequestException as e:
        error_detail = ""
        try:
            error_detail = response.json().get(
                "Message", response.json().get("message", response.text)
            )
        except:
            error_detail = (
                response.text
                if "response" in locals() and hasattr(response, "text")
                else "No additional details."
            )
        st.error(f"Error adding task: {e} - Details: {error_detail}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while adding task: {e}")
        return None


def update_existing_task(task_id, title=None, due_date=None, completed=None):
    if not is_api_configured():
        return None
    payload = {}
    if title is not None:
        payload["title"] = title
    if due_date is not None:
        payload["dueDate"] = due_date
    if completed is not None:
        payload["completed"] = completed

    if not payload:
        st.warning("No changes to update.")
        return None

    try:
        # TASK_ENDPOINT is like ".../tasks", so we append "/{task_id}"
        response = requests.put(f"{TASK_ENDPOINT}/{task_id}", json=payload)
        response.raise_for_status()
        updated_task_data = response.json().get("task", {})
        updated_title = updated_task_data.get("title", task_id)
        st.success(f"Task '{updated_title}' updated successfully!")
        return updated_task_data
    except requests.exceptions.RequestException as e:
        error_detail = ""
        try:
            error_detail = response.json().get(
                "Message", response.json().get("message", response.text)
            )
        except:
            error_detail = (
                response.text
                if "response" in locals() and hasattr(response, "text")
                else "No additional details."
            )
        st.error(f"Error updating task: {e} - Details: {error_detail}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while updating task: {e}")
        return None


def delete_existing_task(task_id):
    if not is_api_configured():
        return None
    try:
        # TASK_ENDPOINT is like ".../tasks", so we append "/{task_id}"
        response = requests.delete(f"{TASK_ENDPOINT}/{task_id}")
        response.raise_for_status()
        # Chalice delete returns a message like {'message': "Task 'id' deleted successfully."}
        st.success(
            response.json().get("message", f"Task '{task_id}' deleted successfully!")
        )
        return True
    except requests.exceptions.RequestException as e:
        error_detail = ""
        try:
            error_detail = response.json().get(
                "Message", response.json().get("message", response.text)
            )
        except:
            error_detail = (
                response.text
                if "response" in locals() and hasattr(response, "text")
                else "No additional details."
            )
        st.error(f"Error deleting task: {e} - Details: {error_detail}")
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred while deleting task: {e}")
        return False


# --- Streamlit UI Layout ---

# Sidebar for adding new tasks
with st.sidebar:
    st.header("➕ Add New Task")
    with st.form("new_task_form", clear_on_submit=True):
        new_title = st.text_input(
            "Title", key="new_title_input"
        )  # Changed key to avoid conflict
        new_due_date_val = st.date_input(
            "Due Date", value=datetime.today(), key="new_due_date_input"  # Changed key
        )
        submitted = st.form_submit_button("Add Task")

        if submitted:
            if not is_api_configured():
                pass  # Warning already shown by is_api_configured
            elif new_title and new_due_date_val:
                if add_new_task(new_title, new_due_date_val.strftime("%Y-%m-%d")):
                    st.rerun()  # To refresh the task list
            else:
                st.warning("Please provide both title and due date.")

# Main area for displaying tasks
if is_api_configured():  # Only attempt to get tasks if API is configured
    tasks = get_all_tasks()

    if (
        not tasks and TASK_ENDPOINT and "execute-api" in TASK_ENDPOINT
    ):  # Second part of condition ensures it's not the initial empty TASK_ENDPOINT
        st.info("No tasks yet, or failed to load. Add one from the sidebar!")
    elif tasks:  # Only proceed if tasks is a non-empty list
        st.subheader("Your Tasks:")

        pending_tasks = [t for t in tasks if not t.get("completed", False)]
        completed_tasks = [t for t in tasks if t.get("completed", False)]

        if pending_tasks:
            st.markdown("---")
            st.markdown("### ⏳ Pending")
            for task in pending_tasks:
                task_id = task.get("taskId")
                # Use a unique prefix for keys inside the loop to ensure they are distinct
                # from keys used for completed tasks or other parts of the UI.
                unique_key_prefix = f"pending_{task_id}"

                col1, col2, col3, col4 = st.columns([0.05, 0.4, 0.25, 0.3])
                with col1:
                    # The checkbox value should reflect the current task's completed status,
                    # which is False for pending tasks.
                    is_checked_by_user = st.checkbox(
                        "", value=False, key=f"{unique_key_prefix}_check"
                    )
                    if is_checked_by_user:  # If user ticks it
                        update_existing_task(task_id, completed=True)
                        st.rerun()
                with col2:
                    st.markdown(f"**{task.get('title', 'N/A')}**")
                    st.caption(f"Due: {task.get('dueDate', 'N/A')}")
                with col3:
                    if st.button("Edit", key=f"{unique_key_prefix}_edit"):
                        with st.expander("Edit Task Details", expanded=True):
                            edit_title = st.text_input(
                                "New Title",
                                value=task.get("title"),
                                key=f"{unique_key_prefix}_edit_title",
                            )
                            current_due_date_str = task.get("dueDate")
                            current_due_date_obj = (
                                datetime.strptime(current_due_date_str, "%Y-%m-%d")
                                if current_due_date_str
                                else datetime.today()
                            )

                            edit_due_date = st.date_input(
                                "New Due Date",
                                value=current_due_date_obj,
                                key=f"{unique_key_prefix}_edit_date",
                            )
                            if st.button(
                                "Save Changes", key=f"{unique_key_prefix}_save_edit"
                            ):
                                if update_existing_task(
                                    task_id,
                                    title=edit_title,
                                    due_date=edit_due_date.strftime("%Y-%m-%d"),
                                ):
                                    st.rerun()
                with col4:
                    if st.button(
                        "Delete 🗑️", key=f"{unique_key_prefix}_del", type="secondary"
                    ):
                        if delete_existing_task(task_id):
                            st.rerun()
                st.markdown("---")
        else:
            if (
                TASK_ENDPOINT and "execute-api" in TASK_ENDPOINT
            ):  # Only show if API is configured
                st.info("No pending tasks!")

        if completed_tasks:
            st.markdown("---")
            st.markdown("### ✅ Completed")
            for task in completed_tasks:
                task_id = task.get("taskId")
                unique_key_prefix = f"completed_{task_id}"

                col1, col2, col3 = st.columns([0.05, 0.65, 0.3])
                with col1:
                    # Checkbox value should be True for completed tasks.
                    is_still_checked = st.checkbox(
                        "", value=True, key=f"{unique_key_prefix}_check"
                    )
                    if not is_still_checked:  # If user unchecks it
                        update_existing_task(task_id, completed=False)
                        st.rerun()
                with col2:
                    st.markdown(f"~~{task.get('title', 'N/A')}~~")
                    st.caption(f"Completed (Due: {task.get('dueDate', 'N/A')})")
                with col3:
                    if st.button(
                        "Delete 🗑️", key=f"{unique_key_prefix}_del", type="secondary"
                    ):
                        if delete_existing_task(task_id):
                            st.rerun()
                st.markdown("---")
    # If tasks list is empty but API was configured (e.g. no tasks in DB yet)
    elif not tasks and TASK_ENDPOINT and "execute-api" in TASK_ENDPOINT:
        st.info("No tasks found. Add one from the sidebar!")
# If API is not configured at all, the warning from is_api_configured() in the sidebar form
# and potentially at the start of the main task display section will be the primary message.
