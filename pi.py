from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import argparse
import pickle
import cv2
import time
import imutils
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import random

servo_pin = 18  # Chân GPIO điều khiển servo
led_pin = 12  # Chân GPIO để điều khiển đèn LED

GPIO.setmode(GPIO.BCM)
GPIO.setup(servo_pin, GPIO.OUT)
GPIO.setup(led_pin, GPIO.OUT)

pwm = GPIO.PWM(servo_pin, 50)  # Tạo tín hiệu PWM với tần số 50Hz (chu kỳ 20ms)
pwm.start(0)  # Bắt đầu PWM với duty cycle 0 (motor dừng)

broker = 'broker.emqx.io'
port = 1883
client_id = f'python-mqtt-{random.randint(0, 1000)}'

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    client = mqtt.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def subscribe(client):
    def on_message(client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))
        if msg.topic == "light":
            if msg.payload == b'on':
                GPIO.output(led_pin, GPIO.HIGH)
            elif msg.payload == b'off':
                GPIO.output(led_pin, GPIO.LOW)
        if msg.topic == "servo":
            position = int(msg.payload)
            if position >= 0 and position <= 180:
                set_angle(position)
    client.subscribe("light")
    client.subscribe("servo")
    client.on_message = on_message

def set_angle(angle):
    duty_cycle = angle / 18.0 + 2.5  # Chuyển đổi góc sang chu kỳ duty cycle
    pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(1)  # Chờ 1 giây để servo đạt được vị trí mới

def run():
    client = connect_mqtt()
    client.loop_start()
    subscribe(client)

ap = argparse.ArgumentParser()
# Đường dẫn đến file encodings đã lưu
ap.add_argument("-e", "--encodings", required=True, help="path to the serialized db of facial encodings")
# Nếu muốn lưu video từ webcam
ap.add_argument("-o", "--output", type=str, help="path to the output video")
ap.add_argument("-y", "--display", type=int, default=1, help="whether or not to display output frame to screen")
# Nếu chạy trên CPU hay embedding devices thì để hog, còn khi tạo encoding vẫn dùng cnn cho chính xác
# Không có GPU thì nên để hog thôi nhé, cứ thử xem sao
ap.add_argument("-d", "--detection_method", type=str, default="hog", help="face detection model to use: cnn or hog")
args = vars(ap.parse_args())

if __name__ == '__main__':
    run()

# Load the known faces and encodings
print("[INFO] loading encodings...")
with open(args["encodings"], "rb") as f:
    data = pickle.load(f)

# Khởi tạo video stream và pointer to the output video file, để camera warm up một chút
print("[INFO] starting video stream...")
vs = VideoStream(src='http://172.20.10.2:8080/video').start()
#vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)

# start the FPS counter
fps = FPS().start()

if args["output"] is not None:
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    writer = cv2.VideoWriter(args["output"], fourcc, 20, (640, 480))

# Loop over frames from the video file stream
while True:
    # Grab the frame from the threaded video stream
    frame = vs.read()

    # Resize the frame to have a width of 500 pixels (just for faster processing)
    frame = imutils.resize(frame, width=500)

    # Convert the input frame from (1) BGR to grayscale (for face detection) and (2) from BGR to RGB (for face recognition)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect faces in the grayscale frame
    rects = face_recognition.face_locations(gray, model=args["detection_method"])

    # OpenCV returns bounding box coordinates in (top, right, bottom, left) order, but we need them in (top, right, bottom, left) order, so we need to rearrange them
    boxes = [(top, right, bottom, left) for (top, right, bottom, left) in rects]

    # Compute the facial embeddings for each face bounding box
    encodings = face_recognition.face_encodings(rgb, boxes)
    names = []

    # Loop over the facial embeddings
    for encoding in encodings:
        # Attempt to match each face in the input image to our known encodings
        matches = face_recognition.compare_faces(data["encodings"], encoding)
        name = "Unknown"  # Tên mặc định là Unknown

        # Check if we have found a match
        if True in matches:
            # Find the indexes of all matched faces and initialize a dictionary to count the total number of times each face was matched
            matched_idxs = [i for (i, b) in enumerate(matches) if b]
            counts = {}

            # Loop over the matched indexes and maintain a count for each recognized face face
            for idx in matched_idxs:
                name = data["names"][idx]
                counts[name] = counts.get(name, 0) + 1

            # Determine the recognized face with the largest number of votes (most frequent)
            name = max(counts, key=counts.get)

        # Update the list of names
        names.append(name)

    # Loop over the recognized faces
    for ((top, right, bottom, left), name) in zip(boxes, names):
        # Draw the predicted face name on the image
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    # If an output video file path has been supplied and the video writer has not been initialized, do so now
    if args["output"] is not None and writer is None:
        writer = cv2.VideoWriter(args["output"], fourcc, 20, (frame.shape[1], frame.shape[0]), True)

    # If the video writer is not None, write the frame to the output video file
    if writer is not None:
        writer.write(frame)

    # Check if the frame should be displayed to the screen
    if args["display"] > 0:
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF

        # Exit loop if 'q' is pressed
        if key == ord("q"):
            break

    # Update the FPS counter
    fps.update()

# Stop the timer and display FPS information
fps.stop()
print("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# Close any open windows
cv2.destroyAllWindows()

# Clean up
vs.stop()
if writer is not None:
    writer.release()
GPIO.cleanup()
