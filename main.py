import glfw
import glfw.GLFW as GLFWC
from OpenGL.GL import *
import numpy as np
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr 
from PIL import Image

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
RETURN_ACTION_CONTINUE = 0
RETURN_ACTION_END = 1

def initialize_glfw():
    glfw.init()
    glfw.window_hint(GLFWC.GLFW_CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(GLFWC.GLFW_CONTEXT_VERSION_MINOR, 1)
    glfw.window_hint(GLFWC.GLFW_OPENGL_PROFILE, GLFWC.GLFW_OPENGL_CORE_PROFILE)
    glfw.window_hint(GLFWC.GLFW_OPENGL_FORWARD_COMPAT, GLFWC.GLFW_TRUE)
    glfw.window_hint(GLFWC.GLFW_DOUBLEBUFFER, GL_FALSE)

    window = glfw.create_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Lab4 Shevchenko", None, None)
    glfw.make_context_current(window)
    glfw.set_input_mode(window, GLFWC.GLFW_CURSOR, GLFWC.GLFW_CURSOR_HIDDEN)

    return window

class App:

    def __init__(self, window):
        self.window = window
        self.renderer = GraphicsEngine()
        self.scene = Scene()

        self.lastTime = glfw.get_time()
        self.currentTime = 0
        self.numFrames = 0
        self.frameTime = 0

        self.walk_offset_lookup = {
            1: 0,
            2: 90,
            3: 45,
            4: 180,
            6: 135,
            7: 90,
            8: 270,
            9: 315,
            11: 0,
            12: 225,
            13: 270,
            14: 180
        }

        self.mainLoop()

    def mainLoop(self):
        running = True

        while(running):
            #проверка событий
            if glfw.window_should_close(self.window) or glfw.get_key(self.window, GLFWC.GLFW_KEY_ESCAPE) == GLFWC.GLFW_PRESS:
                running = False
            
            self.handleKeys()
            self.handleMouse()
            glfw.poll_events()
            self.scene.update(self.frameTime / 16.7)
            self.renderer.render(self.scene)
            self.calculateFramerate()
        self.quit() #выход из приложения

    def handleKeys(self):
        combo_move = 0
        combo_spin_x = 0
        combo_spin_y = 0
        directionModifier = 0

        if glfw.get_key(self.window, GLFWC.GLFW_KEY_W) == GLFWC.GLFW_PRESS:
            combo_move += 1
        if glfw.get_key(self.window, GLFWC.GLFW_KEY_A) == GLFWC.GLFW_PRESS:
            combo_move += 2
        if glfw.get_key(self.window, GLFWC.GLFW_KEY_S) == GLFWC.GLFW_PRESS:
            combo_move += 4
        if glfw.get_key(self.window, GLFWC.GLFW_KEY_D) == GLFWC.GLFW_PRESS:
            combo_move += 8
            
        if combo_move in self.walk_offset_lookup:
            directionModifier = self.walk_offset_lookup[combo_move]
            dPos = [
                0.1 * self.frameTime / 16.7 * np.cos(np.deg2rad(self.scene.camera.theta + directionModifier)),
                0.1 * self.frameTime / 16.7 * np.sin(np.deg2rad(self.scene.camera.theta + directionModifier)),
                0
            ]
            self.scene.move_camera(dPos)
            

    def handleMouse(self):
        (x, y) = glfw.get_cursor_pos(self.window)
        rate = self.frameTime / 16.7
        theta_increment = rate * ((SCREEN_WIDTH / 2) - x)
        phi_increment = rate * ((SCREEN_HEIGHT / 2) - y)
        self.scene.spin_camera(theta_increment, phi_increment)
        glfw.set_cursor_pos(self.window, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

    def calculateFramerate(self):
        self.currentTime = glfw.get_time()
        delta = self.currentTime - self.lastTime
        if (delta >= 1):
            framerate = max(1, int(self.numFrames / delta))
            glfw.set_window_title(self.window, f"{framerate} fps.")
            self.lastTime = self.currentTime
            self.numFrames = -1
            self.frameTime = float(1000.0/max(1, framerate))
        self.numFrames += 1

    def quit(self):
        self.renderer.quit()

class GraphicsEngine:
    def __init__(self):
        self.wood_texture = Material("gfx/wood.png")
        self.cube_mesh = Mesh("models/glass.obj")

        #инициализация opengl
        glClearColor(0.1, 0.2, 0.2, 1)  #цвет фона/очистки

        #создание шейдера
        self.shader = self.createShader("shaders/vertex.txt", "shaders/fragment.txt")        
        glUseProgram(self.shader)
        glUniform1i(glGetUniformLocation(self.shader, "imageTexture"), 0)

        #glEnable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy = 45, aspect = 640 / 480,
            near = 0.1, far = 1000, dtype=np.float32
        )

        glUniformMatrix4fv(
            glGetUniformLocation(self.shader, "projection"),
            1, GL_FALSE, projection_transform
        )

        self.modelMatrixLocation = glGetUniformLocation(self.shader, "model")
        self.viewMatrixLocation = glGetUniformLocation(self.shader, "view")

    def createShader(self, vertexFilepath, fragmentFilepath):
        with open(vertexFilepath, 'r') as f:
            vertex_src = f.readlines()

        with open(fragmentFilepath, 'r') as f:
            fragment_src = f.readlines()

        shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER), compileShader(fragment_src, GL_FRAGMENT_SHADER))

        return shader
    
    def render(self, scene):
        #обновление экрана
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)    #очистка экрана

        glUseProgram(self.shader)

        view_transform = pyrr.matrix44.create_look_at(
            eye = scene.camera.position, 
            target = scene.camera.position + scene.camera.forwards,
            up = scene.camera.up, dtype=np.float32)
        
        glUniformMatrix4fv(self.viewMatrixLocation, 1, GL_FALSE, view_transform)

        self.wood_texture.use()
        glBindVertexArray(self.cube_mesh.vao)

        for cube in scene.cubes:
            model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
            #вращение
            model_transform = pyrr.matrix44.multiply(
                m1 = model_transform, 
                m2 = pyrr.matrix44.create_from_eulers(
                    eulers=np.radians(cube.eulers), dtype=np.float32
                )
            )
            #передвижение
            model_transform = pyrr.matrix44.multiply(
                m1 = model_transform, 
                m2 = pyrr.matrix44.create_from_translation(
                    vec=np.array(cube.position), dtype=np.float32
                )
            )
            glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, model_transform)
            glDrawArrays(GL_TRIANGLES, 0, self.cube_mesh.vertex_count)

        glFlush()

    def quit(self):
        self.cube_mesh.destroy()
        self.wood_texture.destroy()
        glDeleteProgram(self.shader)

class Camera:
    def __init__(self, position):
        self.position = np.array(position, dtype=np.float32)
        self.theta = 0
        self.phi = 0
        self.update_vectors()

    def update_vectors(self):
        self.forwards = np.array(
            [
                np.cos(np.deg2rad(self.theta)) * np.cos(np.deg2rad(self.phi)),
                np.sin(np.deg2rad(self.theta)),
                np.cos(np.deg2rad(self.theta)) * np.sin(np.deg2rad(self.phi)),
            ]
        )

        globalUp = np.array([0, 0, 1], dtype=np.float32)

        self.right = np.cross(self.forwards, globalUp)

        self.up = np.cross(self.right, self.forwards)

class Scene:
    def __init__(self):
        self.cubes = [
            Cube(
                position = [6, 0, 0],
                eulers = [0, 0, 0]
            ),
            Cube(
                position = [0, -3, -4],
                eulers = [0, 0, 0]
            ),
            Cube(
                position = [7, -3, 7],
                eulers = [0, 0, 0]
            )
        ]

        self.camera = Camera(position=[0, 0, 2])

    def update(self, rate):
        for cube in self.cubes:
            cube.eulers[1] += 0.25 * rate
            if cube.eulers[1] > 360:
                cube.eulers[1] -= 360

    def move_camera(self, dPos):
        dPos = np.array(dPos, dtype = np.float32)
        self.camera.position += dPos
    
    def spin_camera(self, dTheta, dPhi):
        self.camera.theta = min(89, max(-89, self.camera.theta + dTheta))
        self.camera.phi = (self.camera.phi + dPhi) % 360

        self.camera.update_vectors()

class Cube:
    def __init__(self, position, eulers):
        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)

class Mesh:
    def __init__(self, filename):
        #x, y, z, s, t, nx, ny, nz
        self.vertices = self.loadMesh(filename)
        self.vertex_count = len(self.vertices) // 8
        self.vertices = np.array(self.vertices, dtype=np.float32)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        #вершины
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        #расположение
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))

        #текстура
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))

    def loadMesh(self, filename: str) -> list[float]:
        v = []
        vt = []
        vn = []

        vertices = []

        with open(filename, 'r') as file:
            line = file.readline()
            while line:
                words = line.split(" ")
                if words[0] == "v":
                    v.append(self.read_vertex_data(words))
                elif words[0] == "vt":
                    vt.append(self.read_texcoord_data(words))
                elif words[0] == "vn":
                    vn.append(self.read_normal_data(words))
                elif words[0] == "f":
                    self.read_face_data(words, v, vt, vn, vertices)
                line = file.readline()

        return vertices
    
    def read_vertex_data(self, words: list[str]) -> list[float]:
        return [
            float(words[1]),
            float(words[2]),
            float(words[3])
        ]
    
    def read_texcoord_data(self, words: list[str]) -> list[float]:
        return [
            float(words[1]),
            float(words[2])
        ]

    def read_normal_data(self, words: list[str]) -> list[float]:
        return [
            float(words[1]),
            float(words[2]),
            float(words[3])
        ]

    def read_face_data(self, words: list[str],
                        v: list[list[float]], vt: list[list[float]], 
                        vn: list[list[float]], vertices: list[float]) -> None:
        triangleCount = len(words) - 3

        for i in range(triangleCount):
            self.make_corner(words[1], v, vt, vn, vertices)
            self.make_corner(words[2 + i], v, vt, vn, vertices)
            self.make_corner(words[3 + i], v, vt, vn, vertices)

    def make_corner(self, corner_description: str,
                    v: list[list[float]], vt: list[list[float]], 
                    vn: list[list[float]], vertices: list[float]) -> None:
        v_vt_vn = corner_description.split("/")
        if (v_vt_vn[0] != '\n'):
            for element in v[int(v_vt_vn[0]) - 1]:
                vertices.append(element)

            for element in vt[int(v_vt_vn[1]) - 1]:
                vertices.append(element)

            for element in vn[int(v_vt_vn[2]) - 1]:
                vertices.append(element)

    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))

class Material:
    def __init__(self, filepath):
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        with Image.open(filepath, mode = 'r') as image:
            image_width, image_height = image.size
            image = image.convert("RGBA")
            img_data = bytes(image.tobytes())
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image_width, image_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        glGenerateMipmap(GL_TEXTURE_2D)

    def use(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture)

    def destroy(self):
        glDeleteTextures(1, (self.texture,))

if __name__ == "__main__":
    window = initialize_glfw()
    myApp = App(window)