import requests
from bs4 import BeautifulSoup
import base64
import os
from datetime import datetime
import logging
import cv2
from pyzbar.pyzbar import decode
from PIL import Image
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_qr_code(url, login_credentials=None, output_dir="qr_codes"):
    """
    Extract QR codes from the specified school website.
    
    Args:
        url (str): The base URL of the school website
        login_credentials (tuple, optional): Username and password for login if required
        output_dir (str): Directory to save extracted QR codes
    
    Returns:
        list: Paths to the extracted QR code images
    """
    session = requests.Session()
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Step 1: Handle login if credentials are provided
    if login_credentials:
        username, password = login_credentials
        
        # Try to find the login endpoint
        try:
            # First check the main page for login forms
            main_response = session.get(url)
            main_soup = BeautifulSoup(main_response.text, 'html.parser')
            
            # Look for login forms
            login_forms = main_soup.find_all('form')
            login_url = None
            
            for form in login_forms:
                action = form.get('action', '')
                if 'login' in action.lower() or any(input_tag.get('name', '').lower() in ['username', 'user', 'email', 'id'] for input_tag in form.find_all('input')):
                    login_url = action if action.startswith(('http://', 'https://')) else url + action
                    break
            
            # If we couldn't find a login form, try common login paths
            if not login_url:
                common_paths = ['Login.aspx?r=s', '/login', '/signin', '/auth/login', '/user/login']
                for path in common_paths:
                    test_url = url + path
                    try:
                        test_response = session.get(test_url)
                        if test_response.status_code == 200 and 'login' in test_response.text.lower():
                            login_url = test_url
                            break
                    except:
                        continue
            
            if login_url:
                logger.info(f"Found login URL: {login_url}")
                
                # Get the login page to find form fields
                login_page = session.get(login_url)
                login_soup = BeautifulSoup(login_page.text, 'html.parser')
                
                # Try to determine the form field names
                username_field = None
                password_field = None
                
                # Look for input fields that might be username/password
                input_fields = login_soup.find_all('input')
                for field in input_fields:
                    field_name = field.get('name', '').lower()
                    field_type = field.get('type', '').lower()
                    
                    if field_type == 'text' or 'user' in field_name or 'email' in field_name or 'id' in field_name:
                        username_field = field.get('name')
                    elif field_type == 'password' or 'pass' in field_name:
                        password_field = field.get('name')
                
                # If we couldn't find the fields, use some common defaults
                if not username_field:
                    username_field = 'username'
                if not password_field:
                    password_field = 'password'
                
                # Prepare login data
                login_data = {
                    username_field: username,
                    password_field: password
                }
                
                # Attempt login
                try:
                    login_response = session.post(login_url, data=login_data)
                    login_response.raise_for_status()
                    logger.info("Login attempt completed")
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Login request encountered an issue: {e}")
            else:
                logger.warning("Couldn't find login URL, proceeding without login")
        except Exception as e:
            logger.error(f"Error during login process: {e}")
    
    # Step 2: Navigate to possible attendance pages
    saved_paths = []
    
    # Try several potential paths where QR codes might be located
    potential_paths = ['TakeAttendanceStd.aspx', '/attendance', '/qr', '/qrcode', '/scan', '/checkin']
    
    for path in potential_paths:
        try:
            page_url = url + path
            logger.info(f"Checking URL: {page_url}")
            
            response = session.get(page_url)
            if response.status_code != 200:
                continue
                
            # Parse the HTML and find QR code images
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for img tags that might contain QR codes
            possible_qr_selectors = [
                "img[src*='qr']",
                "img[src*='QR']",
                "img[src*='attendance']",
                "img[alt*='QR']",
                "img[alt*='qr']",
                "img[alt*='attendance']",
                "img[alt*='code']"
            ]
            
            qr_images = []
            for selector in possible_qr_selectors:
                qr_images.extend(soup.select(selector))
            
            # Find QR codes as base64 encoded images
            base64_images = []
            img_tags = soup.find_all('img')
            
            for img in img_tags:
                src = img.get('src', '')
                if src.startswith('data:image'):
                    base64_images.append(img)
            
            # Combine both types of found images
            all_potential_qr = qr_images + base64_images
            
            if all_potential_qr:
                logger.info(f"Found {len(all_potential_qr)} potential QR images on {page_url}")
                
                # Step 4: Save all potential QR codes
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                for i, img in enumerate(all_potential_qr):
                    src = img.get('src', '')
                    
                    if src.startswith('data:image'):
                        # Handle base64 encoded image
                        try:
                            # Extract the base64 part
                            base64_data = src.split(',')[1]
                            image_data = base64.b64decode(base64_data)
                            
                            # Save the image
                            img_path = os.path.join(output_dir, f"qr_code_{timestamp}_{i}.png")
                            with open(img_path, 'wb') as f:
                                f.write(image_data)
                            saved_paths.append(img_path)
                            logger.info(f"Saved base64 image to {img_path}")
                            
                        except Exception as e:
                            logger.error(f"Failed to save base64 image {i}: {e}")
                            
                    elif src.startswith(('http://', 'https://')):
                        # Handle remote image
                        try:
                            img_response = session.get(src)
                            img_response.raise_for_status()
                            
                            # Save the image
                            img_path = os.path.join(output_dir, f"qr_code_{timestamp}_{i}.png")
                            with open(img_path, 'wb') as f:
                                f.write(img_response.content)
                            saved_paths.append(img_path)
                            logger.info(f"Saved remote image to {img_path}")
                            
                        except Exception as e:
                            logger.error(f"Failed to download remote image {i}: {e}")
                            
                    elif src.startswith('/'):
                        # Handle relative path
                        try:
                            full_url = f"{url}{src}"
                            img_response = session.get(full_url)
                            img_response.raise_for_status()
                            
                            # Save the image
                            img_path = os.path.join(output_dir, f"qr_code_{timestamp}_{i}.png")
                            with open(img_path, 'wb') as f:
                                f.write(img_response.content)
                            saved_paths.append(img_path)
                            logger.info(f"Saved relative path image to {img_path}")
                            
                        except Exception as e:
                            logger.error(f"Failed to download relative path image {i}: {e}")
        
        except Exception as e:
            logger.error(f"Error checking {path}: {e}")
    
    if saved_paths:
        logger.info(f"Saved {len(saved_paths)} potential QR code images to {output_dir}")
        return saved_paths
    else:
        logger.warning("Failed to save any QR code images")
        return None

def decode_qr_content(image_path):
    """
    Attempt to decode the content of a QR code image
    
    Args:
        image_path (str): Path to the QR code image
        
    Returns:
        str: Decoded content or None if decoding fails
    """
    try:
        # Read the image
        image = cv2.imread(image_path)
        
        # Try to decode QR codes in the image
        decoded_objects = decode(image)
        
        # Return the content of the first QR code found
        if decoded_objects:
            return decoded_objects[0].data.decode('utf-8')
        else:
            logger.warning(f"No QR code found in {image_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error decoding QR code: {e}")
        return None
