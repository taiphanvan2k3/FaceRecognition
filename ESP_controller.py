from flask import Blueprint, jsonify, request
import requests

esp8266_bp = Blueprint("esp8266", __name__)
ESP8266_ID = "http://192.168.11.52/"


@esp8266_bp.route("/check_esp", methods=["GET"])
def check_esp():
    try:
        # Make a GET request to the ESP8266 endpoint
        response = requests.get(ESP8266_ID)
        temp = response.content.decode("utf-8")

        # Check if the request was successful
        if response.status_code == 200:
            return jsonify(
                {
                    "status": "success",
                    "message": "ESP8266 connected",
                    "data": temp,
                }
            )
        else:
            return jsonify(
                {
                    "status": "error",
                    "message": f"Failed to connect to ESP8266, status code: {response.status_code}",
                }
            )
    except requests.exceptions.RequestException as e:
        # Handle any exceptions that occur during the request
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"})


@esp8266_bp.route("/led", methods=["GET"])
def change_led_status():
    try:
        location = request.args.get("location")
        status = request.args.get("status", "1")
        intensity = request.args.get("intensity", 255)
        esp_response = requests.get(
            f"{ESP8266_ID}/led",
            params={"location": location, "status": status, "intensity": intensity},
        )

        # Check if the request was successful
        if esp_response.status_code == 200:
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "LED status changed",
                        "data": esp_response.text,
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to change LED status, status code: {esp_response.status_code}",
                    }
                ),
                500,
            )

    except Exception as e:
        return (
            jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}),
            500,
        )


@esp8266_bp.route("/fan", methods=["GET"])
def change_fan_status():
    try:
        location = request.args.get("location")
        status = request.args.get("status")
        esp_response = requests.get(
            f"{ESP8266_ID}/fan", params={"location": location, "status": status}
        )

        # Check if the request was successful
        if esp_response.status_code == 200:
            return jsonify(
                {
                    "status": "success",
                    "message": "Fan status changed",
                    "data": esp_response.text,
                }
            )
        else:
            return jsonify(
                {
                    "status": "error",
                    "message": f"Failed to change fan status, status code: {esp_response.status_code}",
                }
            )
    except Exception as e:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"})


@esp8266_bp.route("/door", methods=["GET"])
def change_door_status():
    try:
        status = request.args.get("status")
        esp_response = requests.get(f"{ESP8266_ID}/door", params={"status": status})

        # Check if the request was successful
        if esp_response.status_code == 200:
            return jsonify(
                {
                    "status": "success",
                    "message": "Door status changed",
                    "data": esp_response.text,
                }
            )
        else:
            return jsonify(
                {
                    "status": "error",
                    "message": f"Failed to change door status, status code: {esp_response.status_code}",
                }
            )
    except Exception as e:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"})
