#!/ usr/bin/python
import cv2
import uuid
from emotionpi import emotion_api
import pyimgur
import numpy as np
import operator
from Tkinter import *
import random
import os
import sys
# from __future__ import print_function
# import easygui

# Initialize variables and parameters
tickCount = 0
showText = False
happiness = 0
emotions = ['anger','contempt','disgust','fear','happiness','neutral','sadness','surprise']
photo = cv2.imread('image.png')
facecount = 0
looping = False
photomode = False
rects = []
currCount = None
click_point = []
click_point_x = -1
click_point_y = -1
currLevel = 0
screenwidth = 1280/2
screenheight = 1024/2

flashon = False
easymode = True
secEmotion = ''
img_name = 'img_'
img_nr = 0
img_end = ".png"
imagepath = ''
showAnalyzing = False
opacity = 0.4
redfactor = 1
_url = 'https://api.projectoxford.ai/emotion/v1.0/recognize'
_key = '1cc9418279ff4b2683b5050cfa6f3785' #Here you have to paste your primary key
_maxNumRetries = 10
result = []
question = "Show anger"
currEmotion = "anger"
static = False
currPosX = -1
currPosY = -1
countx = 0

# Reset the game state
def reset():
    global currLevel
    global currCount
    global countx
    global photomode
    global click_point_y
    global click_point_x
    global showBegin
    global static
    static = False
    currLevel = 0
    currCount = None
    countx = 0
    photomode = False
    click_point_x = -1
    click_point_y = -1
    showBegin = False

# Put text on screen
def addText(frame,text,origin,size = 1.0,color = (255,255,255),thickness=1):
    cv2.putText(frame,text,origin,cv2.FONT_HERSHEY_SIMPLEX, size, color, 2)

# Put game title on screen
def presentation(frame):
    addText(frame,"PartyPi v0.0.1",((screenwidth/5)*4, screenheight/7),color=(68,54,66),size=0.5, thickness=0.5)
    cv2.imshow('PartyPi',frame)

# Check for most recent image number
def get_last_image_nr():
    nr = 0
    for file in os.listdir(os.getcwd()+'/img'):
        if file.endswith(img_end):
            file = file.replace(img_name, '')
            file = file.replace(img_end,'')
            print file
            file_nr = int(file)
            nr = max(nr, file_nr)
    return nr+1

img_nr=get_last_image_nr()

# Mouse click and position
def mouse(event, x, y, flags, param):
    global click_point
    global click_point_x
    global click_point_y
    global currPosX
    global currPosY

    if event == cv2.EVENT_MOUSEMOVE:
        currPosX,currPosY = x,y
        # print x,y
    if event == cv2.EVENT_LBUTTONUP:
        click_point_x,click_point_y = x,y
        # print x,y

# Capture and save photo
def takephoto(frame):
    global img_nr
    global imagepath
    global photo
    imagepath = 'img/'+str(img_name)+str(img_nr)+str(img_end)
    cv2.imwrite(imagepath, frame)
    img_nr += 1
    photo = frame.copy()
    print "capture key pressed"
    upload_img(photo)
    return photo

# Pick a random emotion
def randomemotion(easymode):
    global static
    global currEmotion
    global secCurrEmotion
    
    if tickCount*redfactor > 30 or static:
        static = True
        if easymode:
            return str(currEmotion)
        else: return currEmotion + '+' + secCurrEmotion
    else: 
        currEmotion = random.choice(emotions)
        randnum = (emotions.index(currEmotion) + random.choice(range(1,7)) )% 8
        secCurrEmotion = emotions[randnum]
        if easymode:
            return currEmotion
        else: 
            return currEmotion + '+' + secCurrEmotion

# Display game
def showgame(frame):
    global currCount
    global flashon
    global photomode
    global currLevel
    global click_point_y
    global showAnalyzing
    showBegin = False
    if currLevel is 1:
        
        if easymode:
            cv2.putText( frame, "Show "+randomemotion(easymode)+'_', (screenwidth/5,3*(screenheight/4)), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2 )
        else:
            addText(frame,"Show "+randomemotion(easymode)+'_' , (10,3*screenheight/4))
        if tickCount*redfactor < 70:
            pass
        elif tickCount*redfactor < 80:
            showBegin = True
        elif tickCount*redfactor < 100:
            pass
        elif tickCount*redfactor >= 100 and tickCount*redfactor <= 110:
            showBegin = False
            currCount = 3
            countx = screenwidth-(screenwidth/5)*4
        elif tickCount*redfactor >= 110 and tickCount*redfactor < 120:
            currCount = 2
            countx = screenwidth-(screenwidth/5)*3
        elif tickCount*redfactor >= 120 and tickCount*redfactor < 130:
            currCount = 1
            countx = screenwidth-(screenwidth/5)*2
        elif tickCount*redfactor >= 130 and tickCount*redfactor< 135:
            flashon = True
            if tickCount*redfactor >133:
                showAnalyzing = True
            countx = -100 # make it disappear
        else: 
            flashon = False
            countx = -100 # make it disappear
            photomode = True
            photo = takephoto(frame)
            currLevel = 2
            click_point_y = -1
        if currCount > 0:
            overlay = frame.copy()
            cv2.rectangle(overlay,(0,int(screenheight*(4./5))),(screenwidth,screenheight),(224,23,101), -1)
            cv2.addWeighted(overlay,opacity,frame,1-opacity, 0, frame)
            cv2.putText(frame, str(currCount), (int(countx), int(screenheight*(7./8))), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255),2)
            
        if showBegin:
            cv2.putText(frame, "Begin!", (screenwidth/3,screenheight/2), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255,255,255),2)

def display(result,frame):
    scores = []
    maxfirstemo = -1
    maxsecondemo = -1
    firstEmotion = -1
    if tickCount % 20 == 0: 
        print "Load Display ", tickCount
    for currFace in result:
        faceRectangle = currFace['faceRectangle']
        cv2.rectangle(photo,(faceRectangle['left'],faceRectangle['top']),
                (faceRectangle['left']+faceRectangle['width'], faceRectangle['top'] +
                    faceRectangle['height']), color = (255,255,0), thickness = 5 )

    for idx, currFace in enumerate(result):
        faceRectangle = currFace['faceRectangle']
        # currEmotion = max(currFace['scores'].items(), key=operator.itemgetter(1))[0]
        firstEmotion = currFace['scores'][currEmotion]*100
        secEmotion = currFace['scores'][secCurrEmotion]*100
        #scores.append((firstEmotion+1)+(secEmotion+1))
        scores.append((firstEmotion+1)*(secEmotion+1)*400)
        # if firstEmotion > maxfirstemo:
        #   maxfirstemo = idx
        # if secEmotion > maxsecondemo:
        #   maxsecondemo = idx
        textToWrite = "%i points: %s" % ( firstEmotion, currEmotion)
        secondLine = "%i points: %s" % ( secEmotion, secCurrEmotion)
        if easymode:
            cv2.putText( photo, textToWrite, (faceRectangle['left'],faceRectangle['top']-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (232,167,35), 2 )
        else:
            cv2.putText( photo, textToWrite, (faceRectangle['left'],faceRectangle['top']-40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (232,167,35), 2 )
            cv2.putText( photo, secondLine, (faceRectangle['left'],faceRectangle['top']-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (232,167,35), 2 )
    
    if firstEmotion >= 0:
        winner = scores.index(max(scores))
        firstRectLeft = result[winner]['faceRectangle']['left']
        firstRectTop = result[winner]['faceRectangle']['top']
        if easymode:
            cv2.putText( photo, "Winner: ", (firstRectLeft,firstRectTop-40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (232,167,35), 2 )
        else:
            cv2.putText( photo, "Winner: ", (firstRectLeft,firstRectTop-70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (232,167,35), 2 )
    
##    if currPosY >= screenheight*(4./5) and currPosY < screenheight:
##        
##        cv2.rectangle(overlay,(0,int(screenheight*(4./5))),(screenwidth,screenheight),(224,23,101), -1)
##        cv2.addWeighted(overlay,opacity,photo,1-opacity, 0, frame)
##    else: 
##        pass

    if currLevel == 2:
        print "currLevel is 2"
        overlay = photo.copy()
        if currPosY >= screenheight*(4./5) and currPosY < screenheight:
            cv2.rectangle(overlay,(0,int(screenheight*(3./4))),(screenwidth,screenheight),(224,23,101), -1)
            cv2.addWeighted(overlay,opacity,photo,1-opacity, 0, frame)
        if click_point_y >= screenheight*(4./5) and click_point_y < screenheight:
            print "Restarting"
        cv2.putText( photo, "[Click to play again]", (screenwidth/2, int(screenheight*(6./7))), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (62,184,144), 2) 

def upload_img(frame):
    global showText
    global result
    global currLevel
    print "Initate upload"
    currLevel = 2
    
    CLIENT_ID = "525d3ebc1147459"
    
    im = pyimgur.Imgur(CLIENT_ID)
    uploaded_image = im.upload_image(imagepath, title="Uploaded with PyImgur")
    print(uploaded_image.title)
    print(uploaded_image.link)
    print(uploaded_image.size)
    print(uploaded_image.type)
    
    print "Analyze image"
    data = emotion_api(uploaded_image.link)
    showText = True
    result = data
    display(result,frame)

# Begin main program
# cascPath = "haarcascade_frontalface_default.xml"
# faceCascade = cv2.CascadeClassifier(cascPath)
# flags=cv2.cv.CV_HAAR_SCALE_IMAGE
cam = cv2.VideoCapture(0)
print "Camera initialize"
cam.set(3,screenwidth)
cam.set(4,screenheight)

scale = 0.5 #font scale

looping = True
# cv2.namedWindow('PartyPi',cv2.WINDOW_AUTOSIZE)
cv2.namedWindow('PartyPi',0)
#cv2.setWindowProperty('PartyPi', cv2.WND_PROP_FULLSCREEN, cv2.cv.CV_WINDOW_FULLSCREEN)
cv2.setMouseCallback('PartyPi',mouse)

while looping:
    tickCount += 1
    font = cv2.FONT_HERSHEY_SIMPLEX
     
# Capture frame-by-frame
    ret, frame = cam.read()
    frame = cv2.flip(frame,1)
    overlay = frame.copy()
   # Display the resulting frame
   # Display face / text 
    display(result,frame)
    if currLevel is 0:
        addText(frame,"Easy", (screenwidth/8,(screenheight*3)/4), size=3)
        addText(frame,"Hard", (screenwidth/2,(screenheight*3)/4), size=3)
        if currPosX >= 0 and currPosX < screenwidth/2:
            cv2.rectangle(overlay,(0,0),(screenwidth/2,screenheight),(211,211,211), -1)
        else: 
            cv2.rectangle(overlay,(screenwidth/2,0),(screenwidth,screenheight),(211,211,211), -1)
        if click_point_x >= 0:
            print "click point x is greater than 0"
            if click_point_x < screenwidth/2:
                easymode = True # Easy mode selected
            else: easymode = False # Hard mode selected
            tickCount = 0
            currLevel = 1
        cv2.addWeighted(overlay,opacity,frame,1-opacity, 0, frame)
    elif currLevel == 2:        
##        overlay = frame.copy()
##        if currPosY >= screenheight*(4./5) and currPosY < screenheight:
##            cv2.rectangle(overlay,(0,int(screenheight*(3./4))),(screenwidth,screenheight),(224,23,101), -1)
##            cv2.addWeighted(overlay,opacity,frame,1-opacity, 0, frame)
##            if click_point_y >= screenheight*(4./5) and click_point_y < screenheight:
##            print "Restarting"         
        if click_point_y > 0:
            reset()
    if not photomode:
        showgame(frame)
        if flashon:
            cv2.rectangle(frame,(0,0),(screenwidth,screenheight),(255,255,255), -1)
            if showAnalyzing:
                addText(frame,"Analyzing...",(screenwidth/5,screenheight/4),size=2.2,color=(224,23,101))
        presentation(frame)
    else: #photo mode is on
        showgame(photo)
        presentation(photo)
    keypress = cv2.waitKey(1) & 0xFF
    if keypress != 255:
        print (keypress)
        # if keypress == 32:
            # tickCount = 0
            # photomode = True
            # photo = takephoto()

        if keypress == 113 or 27: # 'q' pressed to quit
            print "Escape key entered"
            looping = False
            break

# When everything is done, release the capture
cam.release()
if photomode: 
    presentation(photo)
else:
    addText(frame,"Press any key to quit_",(screenwidth/4,screenheight/3))
    presentation(frame)

cv2.waitKey(0)
cv2.destroyAllWindows()