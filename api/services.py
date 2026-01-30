import requests
from django.conf import settings
from urllib.parse import urlencode


class SMSPortalService:
    """Service for sending SMS via SMS Portal API"""

    @staticmethod
    def send_sms(phone_number, message):
        """
        Send SMS using SMS Portal API

        Args:
            phone_number: Phone number in international format (e.g., +27821234567)
            message: SMS message text

        Returns:
            dict: Response from SMS Portal API
        """
        try:
            # Clean phone number (remove + and spaces)
            clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')

            # SMS Portal API parameters
            params = {
                'Type': 'sendparam',
                'Username': settings.SMS_PORTAL_USERNAME,
                'Password': settings.SMS_PORTAL_PASSWORD,
                'numto': clean_phone,
                'data1': message,
            }

            # Build URL with parameters
            url = f"{settings.SMS_PORTAL_ENDPOINT}?{urlencode(params)}"

            # Send request
            response = requests.get(url, timeout=30)

            print(f'📱 SMS sent to {phone_number}')
            print(f'📨 Response: {response.text}')

            # Parse response
            # SMS Portal returns format: EventID|Status|Credits
            # Example success: "12345|OK|95.5"
            # Example error: "0|Error|Error description"

            response_parts = response.text.strip().split('|')

            if len(response_parts) >= 2:
                event_id = response_parts[0]
                status = response_parts[1]

                if status == 'OK':
                    return {
                        'success': True,
                        'event_id': event_id,
                        'message': 'SMS sent successfully',
                        'response': response.text
                    }
                else:
                    error_msg = response_parts[2] if len(response_parts) > 2 else 'Unknown error'
                    return {
                        'success': False,
                        'error': error_msg,
                        'response': response.text
                    }
            else:
                return {
                    'success': False,
                    'error': 'Invalid response format',
                    'response': response.text
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'SMS service timeout'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'SMS service error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }

    @staticmethod
    def send_otp(phone_number, otp_code):
        """
        Send OTP code via SMS

        Args:
            phone_number: Phone number in international format
            otp_code: 6-digit OTP code

        Returns:
            dict: Response from SMS Portal API
        """
        message = f"Your CareConnect verification code is: {otp_code}. Valid for 10 minutes. Do not share this code."
        return SMSPortalService.send_sms(phone_number, message)
