import sys, pygame,threading,serial
import Leap, thread, time, math
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture
pygame.init()

ser = serial.Serial('COM14', 115200)
packet = [0,0,0,255]

files = ["1.png","2.png","3.png","4.png","5.png","6.png","7.png","8.png","9.png","10.png","11.png","12.png"]
bgcolors = [(0,0,0),(255,0,0),(0,255,0),(255,255,255),(0,0,255)]
current_bgcolor = 0

size = width, height = 200, 320
speed = [2, 2]

pos_x = width/2
pos_y = height/2
pinch = 0
pinch_l = 0

center_pos = width/2-1+300

screen = pygame.display.set_mode(size)

images = []
for filename in files:
  images.append(pygame.image.load("PixelArt\\"+filename))

curr_img = 0

orn = images[curr_img]
ornaments = []

circle_turns = 0

stop_threads = False

def map_val(val, min_in, max_in, min_out, max_out):
  if val >= max_in:
    return max_out
  elif val <= min_in:
    return min_out
  return ((val-min_in)/(max_in-min_in))*(max_out-min_out) + min_out

def translate(x, offset):
  global width
  
  if (offset-(width/2)) == 0:
    return x
  else:
    x = x + (offset-(width/2))
    if x > width:
      return x - width
    elif x < 0:
      return width + x
    else:
      return x


class SampleListener(Leap.Listener):
  finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
  bone_names = ['Metacarpal', 'Proximal', 'Intermediate', 'Distal']
  state_names = ['STATE_INVALID', 'STATE_START', 'STATE_UPDATE', 'STATE_END']

  def on_init(self, controller):
    print "Initialized"

  def on_connect(self, controller):
    print "Connected"

    # Enable gestures
    controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);
    #controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
    #controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);
    controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);

  def on_disconnect(self, controller):
    # Note: not dispatched when running in a debugger.
    print "Disconnected"

  def on_exit(self, controller):
    print "Exited"

  def on_frame(self, controller):
    global pos_y, pos_x, pinch, pinch_l, ornaments, curr_img, orn,height,width, ser, packet
    frame = controller.frame()
    
    for hand in frame.hands:
      if hand.is_left:
        global current_bgcolor, bgcolors
        pinch_l = hand.pinch_strength
        old_pinch = pinch_l
        if old_pinch > 0.90 and pinch <= 0.90:
          packet[0] = 0
          packet[1] = 2
          packet[2] = 0
          packet[3] = 255
          ser.write(packet)
          del ornaments[:]
          current_bgcolor = 0
  
          
      if hand.is_right:
        for finger in hand.fingers:
          if finger.type == 1:
            bone = finger.bone(1)
            position = hand.direction
            pos = hand.palm_position
            old_pinch = pinch
            pinch = hand.pinch_strength
            pos_y = int(height-map_val(position[1], -0.15, 0.60, 0, height))
            pos_x = width-int(map_val(pos[0], -100.0, 100.0, 0, width))
            
            packet[0] = 1
            packet[1] = 1+int(pos_x/float(width)*254)
            packet[2] = 1+int(pos_y/float(height)*254)
            packet[3] = 255
            ser.write(packet)
            
            if old_pinch > 0.90 and pinch <= 0.90:
              packet[0] = 0
              packet[1] = 0
              packet[2] = 0
              packet[3] = 255
              ser.write(packet)
              
              ornaments.append((orn, (translate(pos_x,center_pos), pos_y)))
              
              orn = images[curr_img]
              
              curr_img = curr_img + 1
              if curr_img==len(images):
                curr_img = 0
    
    for gesture in frame.gestures():
      global current_bgcolor, bgcolors, circle_turns
      if gesture.type == Leap.Gesture.TYPE_CIRCLE:
          circle = CircleGesture(gesture)

          old_turns = circle_turns
          
          print "-"
          print str(circle.progress)
          
          print str(old_turns)
          circle_turns = math.floor(circle.progress)
          print str(circle_turns)
          
          if old_turns == 0 and circle_turns == 1:
          
              packet[0] = 0
              packet[1] = 1
              packet[2] = 0
              packet[3] = 255
              #ser.write(packet)
              #current_bgcolor = current_bgcolor + 1
              #if current_bgcolor==len(bgcolors):
              #  current_bgcolor = 0

  def state_string(self, state):
    print ""

# Create a sample listener and controller
listener = SampleListener()
controller = Leap.Controller()

# Have the sample listener receive events from the controller
controller.add_listener(listener)

buffer =  pygame.Surface((width, height))

def move_bg():
  global center_pos, width
  center_pos = center_pos + 1
  if center_pos >= width:
    center_pos = center_pos-width
  if not stop_threads:
    threading.Timer(0.05, move_bg).start()

move_bg()

def place_surface(surface_org, surface_dst, pos):
  global width
  screen = surface_dst
  orn = surface_org
  pos_x = pos[0]
  pos_y = pos[1]
  screen.blit(orn, orn.get_rect(center = (pos_x, pos_y)))
  if (pos_x+(orn.get_width()/2)) > (width-1):
    ext_crop = (pos_x+(orn.get_width()/2)) - (width-1)
    subsurf1 = orn.subsurface((orn.get_width()-ext_crop,0,ext_crop,orn.get_height()))
    screen.blit(subsurf1, (0, pos_y-(orn.get_height()/2), ext_crop, orn.get_height()))
  if (pos_x-(orn.get_width()/2)) < 0:
    ext_crop = 0 - (pos_x-(orn.get_width()/2))
    subsurf1 = orn.subsurface((0,0,ext_crop,orn.get_height()))
    screen.blit(subsurf1, (width-ext_crop, pos_y-(orn.get_height()/2), ext_crop, orn.get_height()))

while True:
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      stop_threads = True
      sys.exit()
  
  buffer.fill(bgcolors[current_bgcolor])
  for ornament in ornaments:
    place_surface(ornament[0], buffer, ornament[1])
  
  
  if center_pos < ((width/2)-1):
    offset = ((width/2)-1)-center_pos
    subsurf1 = buffer.subsurface((center_pos+(width/2), 0, offset, height))
    subsurf2 = buffer.subsurface((center_pos-(width/2)+offset+1, 0, width-offset, height))
    screen.blit(subsurf1, (0, 0, offset, height))
    screen.blit(subsurf2, (offset, 0, width-offset, height))
  if center_pos == ((width/2)-1):
    screen.blit(buffer, (0, 0, width, height))
  if center_pos > ((width/2)-1):
    offset = center_pos-((width/2)-1)
    subsurf1 = buffer.subsurface((0, 0, offset, height))
    subsurf2 = buffer.subsurface((offset, 0, width-offset, height))
    screen.blit(subsurf1, (width-offset, 0, offset, height))
    screen.blit(subsurf2, (0, 0, width-offset, height))
  
  
  place_surface(orn, screen, (pos_x, pos_y))
  pygame.display.flip()