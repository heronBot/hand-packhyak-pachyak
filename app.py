import cv2
import mediapipe as mp
import pygame,time,socket
import os

pygame.init()


class MainApp():
    def is_hand_closed(self, hand_landmarks):
 

        tip_landmarks = [
            hand_landmarks.landmark[8],   # Index finger tip
            hand_landmarks.landmark[12],  # Middle finger tip
            hand_landmarks.landmark[16],  # Ring finger tip
            hand_landmarks.landmark[20]   # Pinky tip
        ]
        
    
        mcp_landmarks = [
            hand_landmarks.landmark[5],   # Index finger MCP
            hand_landmarks.landmark[9],   # Middle finger MCP
            hand_landmarks.landmark[13],  # Ring finger MCP
            hand_landmarks.landmark[17]   # Pinky MCP
        ]
        
       
        finger_closed_count = 0
        for tip, mcp in zip(tip_landmarks, mcp_landmarks):
           
            vertical_distance = tip.y - mcp.y
      
            horizontal_spread = abs(tip.x - mcp.x)
       
            if vertical_distance > 0.05 and horizontal_spread < 0.03:
                finger_closed_count += 1
        
        
        return finger_closed_count >= 3
    def __init__(self):
        self.screen_width, self.screen_height = 800, 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Hand Gesture File Transfer")

        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)

        self.large_font = pygame.font.Font(None, 72)
        self.medium_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 36)

        self.previous_hand_state = None
        self.hand_closed_start_time = None
        self.transfer_complete = False
        self.transfer_message = ""

        self.time_to_hold = 2

        file = open('toSend.jpg','rb')
        self.toSend = file.read()
        file.close()

        self.client = socket.socket()
        self.client.connect(("192.168.100.4",8084))
        print("CONNECTED")
        self.run()

    
    
    def run(self):
        cap = cv2.VideoCapture(2)
        mp_hands = mp.solutions.hands
        with mp_hands.Hands(
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5,
            max_num_hands=1
        ) as hands:
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
             
            
                ret, frame = cap.read()
                if not ret:
                    print("Failed to capture frame. Exiting...")
                    break

                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb_frame)
                self.screen.fill(self.WHITE)

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        is_closed = self.is_hand_closed(hand_landmarks)

                        if not is_closed and not self.previous_hand_state:
                            print("RECEIVING..")
                            self.client.send(b'get')
                            recv  = self.client.recv(50000000)
                            f = open('recv.jpg','wb')
                            f.write(recv)
                            f.close()
                            self.previous_hand_state = 'closed'
                            print("RECIVED")
                            os.system('recv.jpg')

                    
                        if is_closed and not self.hand_closed_start_time:
                            self.hand_closed_start_time = time.time()
                            self.previous_hand_state = 'close'
                        
                        if not is_closed and self.hand_closed_start_time:
                            self.previous_hand_state = 'open'
                            self.hand_closed_start_time = None
                    
                        if is_closed and self.hand_closed_start_time:
                            if time.time() - self.hand_closed_start_time >= self.time_to_hold:
                                print("SENDING")
                                self.client.send(b'set')
                                self.client.recv(2)
                                self.client.send(self.toSend)
                                self.client.recv(3)
                                self.hand_closed_start_time = None
                
                if self.hand_closed_start_time:
                    remaining = max(0, self.time_to_hold- (time.time() - self.hand_closed_start_time))
                    wait_text = self.medium_font.render(f"Hold: {remaining:.1f} seconds", True, self.BLACK)
                    text_rect = wait_text.get_rect(center=(self.screen_width//2, self.screen_height//2))
                    self.screen.blit(wait_text, text_rect)
                
                else:
                    instruction_text = self.medium_font.render(
                            "Close hand for 4 seconds to transfer", 
                            True, 
                            self.BLACK
                        )
                    text_rect = instruction_text.get_rect(center=(self.screen_width//2, self.screen_height//2))
                    self.screen.blit(instruction_text, text_rect)

                pygame.display.flip()

        cap.release()
        pygame.quit()

if __name__ == "__main__":
    MainApp()
