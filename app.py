from flask import Flask, request, jsonify, send_file
from models.user import User
from models.invite import Invite
from packaging import version  # pip install packaging


app = Flask(__name__)


# Define the latest stable version (in a real app, you might load this from a config file or environment variable)
LATEST_VERSION = "1.1.0"

@app.route('/check-update', methods=['POST'])
def check_update():
    data = request.get_json() or {}
    current_version = data.get('version', '0.0.0')

    # Compare versions using packaging.version
    parsed_current = version.parse(current_version)
    parsed_latest = version.parse(LATEST_VERSION)

    if parsed_current < parsed_latest:
        # Client version is older than the latest stable version
        response = {
            "updateAvailable": True,
            "latestVersion": LATEST_VERSION,
            "downloadURL": "http://127.0.0.1:5000/download",
            "isBeta": False
        }
    elif parsed_current > parsed_latest:
        # Client version is newer than the stable version (i.e. a beta build)
        response = {
            "updateAvailable": False,
            "latestVersion": LATEST_VERSION,
            "isBeta": True,
            "betaWarning": "You are using an unstable beta version. Would you like to update to the stable release?"
        }
    else:
        # Client version matches the latest stable version
        response = {
            "updateAvailable": False,
            "latestVersion": LATEST_VERSION,
            "isBeta": False
        }

    return jsonify(response), 200

@app.route('/download', methods=['GET'])
def download():
    """
    Dynamically serve the latest stable release file.
    Adjust the file path as needed (here we assume a zip file stored in a 'releases' folder).
    """
    # Construct the file path dynamically based on the latest version.
    file_path = f"releases/UniStuHelper_v{LATEST_VERSION}.zip"
    try:
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"File not found or error serving file: {str(e)}"}), 404

@app.route('/register', methods=['POST'])
def register():
    data = request.json or {}

    username = data.get('username')
    password = data.get('password')
    invite_code = data.get('invite_code')

    if not username or not password or not invite_code:
        return jsonify({'error': 'Missing username, password, or invite code'}), 400

    try:
        user = User.create_user(username, password, invite_code)
        return jsonify({'message': 'User created successfully', 'username': user.username, 'invited_by': user.invited_by}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    user = User.find_by_username(username)

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Now include invites_remaining from the user model.
    return jsonify({
        'message': 'Login successful',
        'username': user.username,
        'user_group': user.user_group,
        'invites_remaining': user.invites_remaining
    }), 200

@app.route('/createInvite', methods=['POST'])
def create_invite():
    """
        Creates an invite if the user is allowed:
        - If user is 'admin' group, they can create unlimited invites.
        - If user is 'standard', they must have invites_remaining > 0.

        Request JSON:
        {
          "username": "<your username>",
          "password": "<your password>",
          "expires_in_min": <int> (optional, defaults to 7 days in minutes)
        }
    """
    data = request.json or {}

    username = data.get('username')
    password = data.get('password')
    expires_in_min = data.get('expires_in_min', 10080)

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    user = User.find_by_username(username)

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    if user.user_group != 'admin' and user.invites_remaining <= 0:
        return jsonify({'error': 'No invites remaining'}), 403

    print("test")

    invite = Invite.create_invite(expires_in_min, user)

    return jsonify({'message': 'Invite created', 'code': invite.code, 'expires_at': invite.expires_at.isoformat(), 'invites_remaining': user.invites_remaining}), 201

if __name__ == '__main__':
    app.run()
