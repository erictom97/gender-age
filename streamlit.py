import streamlit as st
import cv2
import argparse
from PIL import Image
import numpy as np

def highlightFace(net, frame, conf_threshold=0.7):
    frameOpencvDnn = frame.copy()
    frameHeight = frameOpencvDnn.shape[0]
    frameWidth = frameOpencvDnn.shape[1]
    blob = cv2.dnn.blobFromImage(frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False)
    net.setInput(blob)
    detections = net.forward()
    faceBoxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            x1 = int(detections[0, 0, i, 3] * frameWidth)
            y1 = int(detections[0, 0, i, 4] * frameHeight)
            x2 = int(detections[0, 0, i, 5] * frameWidth)
            y2 = int(detections[0, 0, i, 6] * frameHeight)
            faceBoxes.append([x1, y1, x2, y2])
            cv2.rectangle(frameOpencvDnn, (x1, y1), (x2, y2), (0, 255, 0), int(round(frameHeight / 150)), 8)
    return frameOpencvDnn, faceBoxes

def load_models():
    faceProto = "opencv_face_detector.pbtxt"
    faceModel = "opencv_face_detector_uint8.pb"
    ageProto = "age_deploy.prototxt"
    ageModel = "age_net.caffemodel"
    genderProto = "gender_deploy.prototxt"
    genderModel = "gender_net.caffemodel"
    
    faceNet = cv2.dnn.readNet(faceModel, faceProto)
    ageNet = cv2.dnn.readNet(ageModel, ageProto)
    genderNet = cv2.dnn.readNet(genderModel, genderProto)
    
    return faceNet, ageNet, genderNet

def predict_age_gender(faceNet, ageNet, genderNet, frame, faceBoxes):
    MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
    ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
    genderList = ['Male', 'Female']
    padding = 20
    
    results = []
    for faceBox in faceBoxes:
        face = frame[max(0, faceBox[1] - padding):min(faceBox[3] + padding, frame.shape[0] - 1),
                     max(0, faceBox[0] - padding):min(faceBox[2] + padding, frame.shape[1] - 1)]
        blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
        
        genderNet.setInput(blob)
        genderPreds = genderNet.forward()
        gender = genderList[genderPreds[0].argmax()]
        
        ageNet.setInput(blob)
        agePreds = ageNet.forward()
        age = ageList[agePreds[0].argmax()]
        
        results.append((gender, age[1:-1]))
    
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', type=str, help='Path to the image file')
    args = parser.parse_args()
    
    faceNet, ageNet, genderNet = load_models()
    
    if args.image:
        image = cv2.imread(args.image)
        resultImg, faceBoxes = highlightFace(faceNet, image)
        if not faceBoxes:
            print("No face detected")
        else:
            results = predict_age_gender(faceNet, ageNet, genderNet, image, faceBoxes)
            for (gender, age) in results:
                print(f'Gender: {gender}, Age: {age} years')
                cv2.putText(resultImg, f'{gender}, {age}', (faceBoxes[0][0], faceBoxes[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.imshow("Detecting age and gender", resultImg)
            cv2.waitKey(0)
    else:
        st.title("Age and Gender Detection")
        st.write("Use your camera to detect age and gender in real-time or upload an image.")
        
        camera_image = st.camera_input("Take a picture")
        
        if camera_image:
            image = Image.open(camera_image)
            image = np.array(image)
            resultImg, faceBoxes = highlightFace(faceNet, image)
            if not faceBoxes:
                st.write("No face detected")
            else:
                results = predict_age_gender(faceNet, ageNet, genderNet, image, faceBoxes)
                for (gender, age) in results:
                    st.write(f'Gender: {gender}, Age: {age} years')
                    cv2.putText(resultImg, f'{gender}, {age}', (faceBoxes[0][0], faceBoxes[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
                st.image(resultImg, caption="Processed Image", use_column_width=True)
        
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            image = np.array(image)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            resultImg, faceBoxes = highlightFace(faceNet, image)
            if not faceBoxes:
                st.write("No face detected")
            else:
                results = predict_age_gender(faceNet, ageNet, genderNet, image, faceBoxes)
                for (gender, age) in results:
                    st.write(f'Gender: {gender}, Age: {age} years')
                    cv2.putText(resultImg, f'{gender}, {age}', (faceBoxes[0][0], faceBoxes[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
                st.image(resultImg, caption="Processed Image", use_column_width=True)

if __name__ == "__main__":
    main()