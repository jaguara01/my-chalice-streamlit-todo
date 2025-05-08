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


# def add_new_task(title, due_date):
#     if not is_api_configured():
#         return None
#     payload = {"title": title, "dueDate": due_date}
#     try:
#         response = requests.post(TASK_ENDPOINT, json=payload)
#         response.raise_for_status()
#         added_task_data = response.json().get("task", {})
#         added_title = added_task_data.get("title", title)
#         st.success(f"Task '{added_title}' added successfully!")
#         return added_task_data
#     except requests.exceptions.RequestException as e:
#         error_detail = ""
#         try:
#             error_detail = response.json().get(
#                 "Message", response.json().get("message", response.text)
#             )
#         except:
#             error_detail = (
#                 response.text
#                 if "response" in locals() and hasattr(response, "text")
#                 else "No additional details."
#             )
#         st.error(f"Error adding task: {e} - Details: {error_detail}")
#         return None
#     except Exception as e:
#         st.error(f"An unexpected error occurred while adding task: {e}")
#         return None


def update_existing_task(task_id, title=None, due_date=None, completed=None):
    if not is_api_configured():
        st.error("API URL not configured. Cannot update task.")
        return None

    payload = {}
    if (
        title is not None
    ):  # Only add if not None (Streamlit inputs might send empty strings for text)
        payload["title"] = title
    if due_date is not None:
        payload["dueDate"] = due_date
    if completed is not None:
        payload["completed"] = completed

    # --- Add this for debugging ---
    st.write("--- Streamlit: update_existing_task ---")
    st.write(f"Task ID: {task_id}")
    st.write(f"Payload being sent: {payload}")
    st.write(f"Attempting to PUT to: {TASK_ENDPOINT}/{task_id}")
    st.write("--- End Streamlit Debug ---")
    # --- End debugging ---

    if not payload:  # No actual changes were passed other than potentially None values
        st.warning(
            "No actual changes to update (e.g., title wasn't changed or was cleared)."
        )
        # If you want to allow clearing title/date by sending empty strings,
        # then the backend needs to handle empty strings appropriately.
        # For now, if payload is empty, we might not even make the call,
        # unless an empty title/date is a valid state you want to save.
        # Let's assume for now we proceed if payload has anything.
        if not completed is None:  # If only 'completed' was changed, proceed
            pass  # allow just completed status to change
        else:  # if no title, no due_date, and no completed status change
            # This check might be too aggressive if empty strings are valid updates
            # For now, let's rely on the backend to handle the payload it receives.
            pass

    # The original check for an empty payload was good.
    # If title, due_date, AND completed are all None, then payload would be empty.
    if not payload:
        st.warning("No changes detected to update.")
        return None  # Or just return the original task if no changes.

    try:
        response = requests.put(f"{TASK_ENDPOINT}/{task_id}", json=payload)
        response.raise_for_status()
        updated_task_data = response.json().get("task", {})
        updated_title = updated_task_data.get("title", task_id)
        st.success(f"Task '{updated_title}' updated successfully!")
        return updated_task_data
    # ... (rest of your error handling) ...
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


def add_new_task(title, due_date):
    if not is_api_configured():
        st.sidebar.error("API URL not configured. Cannot add task.")
        return None
    payload = {"title": title, "dueDate": due_date}
    try:
        response = requests.post(TASK_ENDPOINT, json=payload)

        # --- BEGIN DEBUGGING ---
        st.write("--- Add Task Debug Info (Frontend) ---")
        st.write(f"Request URL: POST {TASK_ENDPOINT}")
        st.write(f"Request Payload: {payload}")
        st.write(f"Response Status Code: {response.status_code}")
        st.write(f"Response Headers: {response.headers}")
        try:
            parsed_json_response = response.json()
            st.write(f"Response Parsed JSON Type: {type(parsed_json_response)}")
            st.write(f"Response Parsed JSON Content: {parsed_json_response}")
        except requests.exceptions.JSONDecodeError as json_err:
            st.error(f"Response Failed to parse as JSON: {json_err}")
            st.write(f"Response Raw Text: {response.text}")
            st.error(
                f"Error adding task: Backend response was not valid JSON. Raw text: {response.text}"
            )
            return None  # Exit early if not valid JSON
        st.write("--- End Add Task Debug Info (Frontend) ---")
        # --- END DEBUGGING ---

        response.raise_for_status()  # Check for HTTP errors (4xx or 5xx)

        # Use the parsed_json_response from the debugging block
        # This is the line that was likely causing the error if parsed_json_response is a list
        added_task_data = parsed_json_response.get(
            "task", {}
        )  # This line will error if parsed_json_response is a list
        added_title = added_task_data.get("title", title)

        st.success(f"Task '{added_title}' added successfully!")
        return added_task_data
    except requests.exceptions.RequestException as e:
        # ... (rest of your error handling) ...
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
        st.error(f"Error adding task (HTTP Error): {e} - Details: {error_detail}")
        return None
    except AttributeError as ae:
        st.error(
            f"An unexpected error occurred while processing the response from adding a task (AttributeError): {ae}"
        )
        st.error(
            "This usually means the backend sent data in an unexpected format (e.g., a list where a dictionary was expected)."
        )
        st.error(
            "Please check the debug output above if available, and your Chalice backend logs."
        )
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while adding task: {e}")
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
# --- Streamlit UI Layout ---

# Initialize session state for editing if it doesn't exist
# Put this near the top of your script, after imports but before UI elements generally
if "editing_task_id" not in st.session_state:
    st.session_state.editing_task_id = (
        None  # Will store the ID of the task being edited, or None
    )

# --- Sidebar for adding new tasks ---
# (Your sidebar code remains the same)
with st.sidebar:
    st.header("➕ Add New Task")
    with st.form("new_task_form", clear_on_submit=True):
        new_title = st.text_input("Title", key="new_title_input")
        new_due_date_val = st.date_input(
            "Due Date", value=datetime.today(), key="new_due_date_input"
        )
        submitted = st.form_submit_button("Add Task")

        if submitted:
            if not is_api_configured():
                # Warning shown by is_api_configured or individual functions
                pass
            elif new_title and new_due_date_val:
                if add_new_task(new_title, new_due_date_val.strftime("%Y-%m-%d")):
                    st.session_state.editing_task_id = (
                        None  # Close any open editor after adding
                    )
                    st.rerun()
            else:
                st.warning("Please provide both title and due date.")


# --- Main area for displaying tasks ---
if not is_api_configured():
    st.warning(
        "Please enter your Chalice API URL in the text input above to load and manage tasks."
    )
else:
    tasks = get_all_tasks()

    if not tasks:
        st.info("No tasks yet, or failed to load. Add one from the sidebar!")
    else:
        st.subheader("Your Tasks:")

        pending_tasks = [t for t in tasks if not t.get("completed", False)]
        completed_tasks = [t for t in tasks if t.get("completed", False)]

        if pending_tasks:
            st.markdown("---")
            st.markdown("### ⏳ Pending")
            for task in pending_tasks:
                task_id = task.get("taskId")
                # Unique prefix for keys based on task ID
                unique_key_prefix = f"pending_{task_id}"

                col1, col2, col3, col4 = st.columns([0.05, 0.4, 0.25, 0.3])

                # --- Column 1: Checkbox ---
                with col1:
                    is_checked_by_user = st.checkbox(
                        "", value=False, key=f"{unique_key_prefix}_check"
                    )
                    if is_checked_by_user:
                        # If completing a task that was being edited, close the editor
                        if st.session_state.editing_task_id == task_id:
                            st.session_state.editing_task_id = None
                        update_existing_task(task_id, completed=True)
                        st.rerun()

                # --- Column 2: Title and Date ---
                with col2:
                    st.markdown(f"**{task.get('title', 'N/A')}**")
                    st.caption(f"Due: {task.get('dueDate', 'N/A')}")

                # --- Column 3: Edit Button ---
                with col3:
                    # Edit button now just sets the session state flag
                    if st.button("Edit", key=f"{unique_key_prefix}_edit_action"):
                        st.session_state.editing_task_id = (
                            task_id  # Set which task to edit
                        )
                        st.rerun()  # Rerun to display the editor

                # --- Column 4: Delete Button ---
                with col4:
                    if st.button(
                        "Delete 🗑️", key=f"{unique_key_prefix}_del", type="secondary"
                    ):
                        # If deleting a task that was being edited, close the editor
                        if st.session_state.editing_task_id == task_id:
                            st.session_state.editing_task_id = None
                        if delete_existing_task(task_id):
                            st.rerun()

                # --- Conditionally Display Edit Form based on Session State ---
                if st.session_state.editing_task_id == task_id:
                    # Use an expander or just draw the form directly
                    with st.expander("✏️ Edit Task Details", expanded=True):
                        # Use st.form for the edit inputs and save button
                        with st.form(key=f"{unique_key_prefix}_edit_form"):
                            edit_title = st.text_input(
                                "New Title",
                                value=task.get("title"),  # Pre-fill with current title
                                key=f"{unique_key_prefix}_edit_title_input",
                            )
                            current_due_date_str = task.get("dueDate")
                            current_due_date_obj = (
                                datetime.strptime(current_due_date_str, "%Y-%m-%d")
                                if current_due_date_str
                                else datetime.today()
                            )
                            edit_due_date = st.date_input(
                                "New Due Date",
                                value=current_due_date_obj,  # Pre-fill with current date
                                key=f"{unique_key_prefix}_edit_date_input",
                            )

                            # The button inside the form triggers the form submission
                            save_submitted = st.form_submit_button("Save Changes")

                            if save_submitted:
                                st.write(
                                    f"--- Save Changes Submitted for task {task_id}! ---"
                                )  # Debug
                                success = update_existing_task(
                                    task_id,
                                    title=edit_title,  # Use current value from input
                                    due_date=edit_due_date.strftime(
                                        "%Y-%m-%d"
                                    ),  # Use current value from input
                                )
                                if (
                                    success
                                ):  # update_existing_task returns the updated task dict on success, None on failure
                                    st.session_state.editing_task_id = (
                                        None  # Close the editor
                                    )
                                    st.rerun()  # Refresh list
                                # Error messages are handled within update_existing_task

                        # Add a separate "Cancel" button outside the form
                        if st.button(
                            "Cancel Edit", key=f"{unique_key_prefix}_cancel_edit"
                        ):
                            st.session_state.editing_task_id = (
                                None  # Clear the editing flag
                            )
                            st.rerun()  # Rerun to hide the editor

                st.markdown("---")  # Separator after each task item / editor

        else:
            # Only show this if the API is configured but no tasks are pending
            if is_api_configured():
                st.info("No pending tasks!")

        # --- Completed Tasks Section ---
        # (Your code for completed tasks remains the same)
        if completed_tasks:
            st.markdown("---")
            st.markdown("### ✅ Completed")
            for task in completed_tasks:
                # ... (display completed tasks - no edit needed here typically) ...
                task_id = task.get("taskId")
                unique_key_prefix = f"completed_{task_id}"

                col1, col2, col3 = st.columns([0.05, 0.65, 0.3])
                with col1:
                    is_still_checked = st.checkbox(
                        "", value=True, key=f"{unique_key_prefix}_check"
                    )
                    if not is_still_checked:
                        # If unchecking a task that was being edited (unlikely but possible), close editor
                        if st.session_state.editing_task_id == task_id:
                            st.session_state.editing_task_id = None
                        update_existing_task(task_id, completed=False)
                        st.rerun()
                with col2:
                    st.markdown(f"~~{task.get('title', 'N/A')}~~")
                    st.caption(f"Completed (Due: {task.get('dueDate', 'N/A')})")
                with col3:
                    if st.button(
                        "Delete 🗑️", key=f"{unique_key_prefix}_del", type="secondary"
                    ):
                        # If deleting a task that was being edited (unlikely but possible), close editor
                        if st.session_state.editing_task_id == task_id:
                            st.session_state.editing_task_id = None
                        if delete_existing_task(task_id):
                            st.rerun()
                st.markdown("---")

        # If tasks list is empty overall (and API was configured)
        elif not tasks and is_api_configured():
            st.info("No tasks found. Add one from the sidebar!")
