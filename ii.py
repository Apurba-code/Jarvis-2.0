import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

def generate_particles(num_particles=15000):
    particles = []

    # 1. Glowing Yellow Core inside head
    for _ in range(3000):
        r = np.random.uniform(0.05, 0.38)
        theta = np.random.uniform(0, 2 * np.pi)
        phi = np.random.uniform(0, np.pi)
        
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.cos(phi) + 0.55
        z = r * np.sin(phi) * np.sin(theta)

        # Bright glowing yellow/orange core
        particles.append([x, y, z, 1.0, 0.75, 0.1, 0.8, 0.022])

    # 2. Concentric Ring Shells (Cyan / Blue Head Surface)
    num_layers = 25
    for layer in range(num_layers):
        y_val = 0.1 + (layer / num_layers) * 0.95
        
        # Head contour radius along height
        rad = np.sqrt(max(0.01, 0.22 - (y_val - 0.55)**2)) * 1.3
        dots_per_ring = int(250 * rad + 30)

        for i in range(dots_per_ring):
            angle = (2 * np.pi / dots_per_ring) * i
            
            x = rad * np.cos(angle) + np.random.normal(0, 0.008)
            y = y_val + np.random.normal(0, 0.005)
            z = rad * np.sin(angle) + np.random.normal(0, 0.008)

            # Particles near top disperse outward
            if y_val > 0.85 and np.random.rand() > 0.4:
                x += np.random.uniform(-0.15, 0.15)
                y += np.random.uniform(0.0, 0.2)
                z += np.random.uniform(-0.15, 0.15)

            # Cyan / Aqua Blue
            particles.append([x, y, z, 0.1, 0.95, 1.0, 0.85, 0.018])

    # 3. Shoulder Lines & Golden Chest/Neck Tendrils
    for u in np.linspace(-1.6, 1.6, 120):
        for v in np.linspace(-0.8, 0.1, 60):
            x = u
            y = v - 0.2 - 0.18 * (u**2)
            z = 0.2 * np.cos(u * 2)

            # Gold / Yellow tendrils in the center neck
            if abs(u) < 0.35 and y > -0.5:
                particles.append([x, y, z, 1.0, 0.6, 0.05, 0.9, 0.02])
            else:
                # Cyan/Blue shoulders
                particles.append([x, y, z, 0.0, 0.8, 0.95, 0.5, 0.015])

    return np.array(particles, dtype=np.float32)

def main():
    pygame.init()
    display = (900, 900)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("3D Particle Mannequin")

    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glTranslatef(0.0, -0.1, -3.8)

    # Enable Additive Blending for high-tech neon glow
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glEnable(GL_POINT_SMOOTH)

    particles = generate_particles()
    angle = 0
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        
        # Micro rotation to emphasize 3D shape
        glRotatef(angle, 0, 1, 0)

        for p in particles:
            x, y, z, r, g, b, alpha, size = p
            
            # Depth scaling & intensity
            depth = (z + 1.5) / 3.0
            depth = np.clip(depth, 0.35, 1.0)

            glColor4f(r * depth, g * depth, b * depth, alpha)
            glPointSize(120.0 * size * depth)

            glBegin(GL_POINTS)
            glVertex3f(x, y, z)
            glEnd()

        glPopMatrix()
        pygame.display.flip()
        
        angle += 0.25
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()