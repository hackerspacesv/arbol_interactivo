import sys, pygame,threading,serial
pygame.init()

ser = serial.Serial('COM14', 115200)
packet = [0,0,0,255]

files = ["1.png","2.png","3.png","4.png","5.png","6.png","7.png","8.png","9.png","10.png","11.png","12.png"]
bgcolors = [(0,0,0),(255,0,0),(0,255,0),(255,255,255),(0,0,255)]
current_bgcolor = 0

size = width, height = 240, 320
speed = [2, 2]

pos_x = width/2
pos_y = height/2
pinch = 0

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
      
  if ser.inWaiting()>0:
    data = bytearray(ser.read(1))
    if data[0] == 1:
      packet = bytearray(ser.read(3))
      pos_x = width-(packet[0]-1)/float(254) * width
      pos_y = (packet[1]-1)/float(254) * height
    if data[0] == 0:
      packet = bytearray(ser.read(3))
      if packet[0] == 0:
        ornaments.append((orn, (translate(pos_x,center_pos), pos_y)))
        
        orn = images[curr_img]
        
        curr_img = curr_img + 1
        if curr_img==len(images):
          curr_img = 0
      if packet[0] == 1:
        current_bgcolor = current_bgcolor + 1
        if current_bgcolor==len(bgcolors):
          current_bgcolor = 0
      if packet[0] == 2:
        del ornaments[:]
        current_bgcolor = 0
  
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