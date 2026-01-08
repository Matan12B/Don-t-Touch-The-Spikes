import pygame


class Bird:
    def __init__(self, bird_data):
        self.jumped = False
        self.name = bird_data[0]
        self.x = bird_data[1]
        self.y = bird_data[2]
        self.width = bird_data[4]
        self.height = bird_data[3]
        self.xSpeed = bird_data[5]
        self.ySpeed = 0
        self.gravity = 2
        self.last_x = self.x
        self.xDirection = bird_data[6]
        self.yDirection = bird_data[7]
        self.alive = True
        self.score = 0

    def jump(self):
        self.ySpeed = -15
        self.jumped = True

    def moveX(self, walls):
        """
        move the bird
        :return:
        """
        # looking to the right
        if self.xDirection and self.x + self.xSpeed < walls[1]-self.width:
            self.x += self.xSpeed
        # looking to the left
        elif not self.xDirection and self.x - self.xSpeed > walls[0]:
            self.x -= self.xSpeed
        else:
            self._if_x_wall_hit(walls)

    def _if_x_wall_hit(self, walls):
        """
        change the direction of the bird and set its x value to the wall
        :param p: list
        :return: None
        """
        if self.x != self.last_x:
            if self.xDirection:
                self.x = walls[1] - self.width
            else:
                self.x = walls[0]
            self.xDirection = not self.xDirection
            self.last_x = self.x
            self.score += 1
            self.hit = True


    def moveY(self, walls):
        """
        :param walls:
        :return:
        """

        # Apply gravity to ySpeed (gravity is a constant force)
        self.ySpeed += self.gravity  # Increase the downward speed due to gravity
        self.y += self.ySpeed  # Update the bird's vertical position based on the speed

        # If the bird hits the bottom (or top), stop it from moving further (clamp it)
        if self.y + self.height >= walls[1]:
            self.y = walls[1] - self.height  # Clamp the bird to the bottom of the screen
            self.ySpeed = 0  # Stop the downward speed after hitting the ground
        elif self.y <= walls[0]:
            self.y = walls[0]  # Clamp the bird to the top of the screen
            self.ySpeed = 0  # Stop the upward speed after hitting the ceiling

    def create_bird_data(self):
        """
        create a dict of all the bird data
        :return:
        """
        data_list = [
            self.name, self.x, self.y,
            self.height, self.width,
            self.xSpeed, self.xDirection, self.yDirection
        ]
        return data_list


class BirdSprite(pygame.sprite.Sprite):
    def __init__(self, image_path, x, y, width, height):
        super().__init__()
        try:
            self.image = pygame.image.load(image_path)
        except pygame.error as e:
            print(f"Error loading image: {image_path}, {e}")
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image = pygame.transform.scale(self.image, (width, height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class PygameBird(Bird):
    def __init__(self, bird_data, image_path, color):
        super().__init__(bird_data)
        self.sprite = BirdSprite(image_path, self.x, self.y, self.width, self.height)
        self.alive = True
        self.color = color

    def update(self, x, y, direct, alive, score):
        self.x = x
        self.y = y
        self.xDirection = direct
        self.update_img(direct)
        self.sprite.update(x, y)
        self.alive = alive
        self.score = score

    def update_img(self, direct):
        """
        change img
        :param direct: the direction the bird is moving
        :param color: blue or purple
        :return:
        """
        # blue
        if self.color == 0:
            if direct:
                new_img_path = "images/bluebird.png"
            else:
                new_img_path = "images/bluebird_left.png"
        # purple
        else:
            if direct:
                new_img_path = "images/purpleBird.png"
            else:
                new_img_path = "images/purpleBird_left.png"
        self.sprite = BirdSprite(new_img_path, self.x, self.y, self.width, self.height)


# spikes
class Spike:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.animation_speed = 5

    def draw_up(self, display, pos):
        """Draws an upward-pointing triangle with the apex (top vertex) at pos."""
        p1 = pos  # Apex (top vertex)
        p2 = (pos[0] - self.width // 2, pos[1] + self.height)  # Left vertex (bottom base)
        p3 = (pos[0] + self.width // 2, pos[1] + self.height)  # Right vertex (bottom base)
        pygame.draw.polygon(display, (100, 100, 100), [p1, p2, p3])

    def draw_down(self, display, pos):
        """Draws an upside-down triangle with the apex (bottom vertex) at pos."""
        p1 = pos  # Apex (bottom vertex)
        p2 = (pos[0] - self.width // 2, pos[1] - self.height)  # Left vertex (top base)
        p3 = (pos[0] + self.width // 2, pos[1] - self.height)
        # Draw the upside-down triangle (spike) with black color
        pygame.draw.polygon(display, (100, 100, 100), [p1, p2, p3])

    def draw_side_spike(self, display, pos, ):
        # Define the points for the flipped shape
        p1 = (pos[0], pos[1] - self.height // 2)
        p2 = (pos[0] - self.width // 2, pos[1])
        p3 = (pos[0], pos[1] + self.height // 2)
        p4 = (pos[0] + self.width // 2 ,pos[1])
        # Draw the polygon
        pygame.draw.polygon(display, (100, 100, 100), [p1, p2, p3, p4])


