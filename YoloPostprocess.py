import numpy as np
import cv2


def post_process(net, thresh, frame, out):
    with open("yolo/classes.data", 'rt') as f:
        classes = f.read().rstrip('\n').split('\n')

    frameHeight = frame.shape[0]
    frameWidth = frame.shape[1]

    def draw_predictions(classId, conf, left, top, right, bottom):
        # Draw a bounding box.
        color = (np.random.rand(3) * 255).tolist()
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

        label = '%.2f' % confidence

        # Print a label of class.
        if classes:
            assert(classId < len(classes))
            label = '%s: %s' % (classes[classId], label)

        labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        top = max(top, labelSize[1])
        cv2.rectangle(frame, (left + 10, top - labelSize[1] - 5), (left + labelSize[0] + 10, top), color, cv2.FILLED)
        cv2.putText(frame, label, (left + 10, top - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0))

    for detection in out:
        confidences = detection[5:]
        classId = np.argmax(confidences)
        confidence = confidences[classId]
        if confidence > thresh:
            center_x = int(detection[0] * frameWidth)
            center_y = int(detection[1] * frameHeight)
            width = int(detection[2] * frameWidth)
            height = int(detection[3] * frameHeight)
            left = int(center_x - width / 2)
            top = int(center_y - height / 2)
            draw_predictions(classId, confidence, left, top, left + width, top + height)
