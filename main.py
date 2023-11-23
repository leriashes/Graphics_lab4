import glfw
import glfw.GLFW as GLFWC
from OpenGL.GL import *
import numpy as np
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr 
from PIL import Image

SCREEN_WIDTH = 1640
SCREEN_HEIGHT = 880

ENTITY_TYPE = {
    "CARPET": 0,
    "POINTLIGHT": 1,
    "FLOOR": 2,
    "CUBE": 100,
    "GLASS": 200,
}

UNIFORM_TYPE = {
    "AMBIENT": 0,
    "VIEW": 1,
    "PROJECTION": 2,
    "CAMERA_POS": 3,
    "LIGHT_COLOR": 4,
    "LIGHT_POS": 5,
    "LIGHT_STRENGTH": 6,
    "TINT": 7,
    "MODEL": 8,
}

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
                0.5 * self.frameTime / 16.7 * np.cos(np.deg2rad(-self.scene.camera.phi + directionModifier)),
                0,
                -0.5 * self.frameTime / 16.7 * np.sin(np.deg2rad(-self.scene.camera.phi + directionModifier)),
            ]
            self.scene.move_camera(dPos)
            
    def handleMouse(self):
        (x, y) = glfw.get_cursor_pos(self.window)
        rate = self.frameTime / 16.7
        phi_increment = rate * ((SCREEN_WIDTH / 2) - x)
        theta_increment = rate * ((SCREEN_HEIGHT / 2) - y)
        self.scene.spin_camera(phi_increment, theta_increment)
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

#камера
class Camera:
    def __init__(self, position):
        self.position = np.array(position, dtype=np.float32)
        self.theta = 0
        self.phi = 0
        self.update()

    def update(self):
        self.forwards = np.array(
            [
                np.cos(np.deg2rad(self.theta)) * np.cos(np.deg2rad(self.phi)),
                np.sin(np.deg2rad(self.theta)),
                np.cos(np.deg2rad(self.theta)) * np.sin(np.deg2rad(self.phi)),
            ]
        )

        globalUp = np.array([0, 1, 0], dtype=np.float32)

        self.right = np.cross(self.forwards, globalUp)

        self.up = np.cross(self.right, self.forwards)

#сцена
class Scene:
    def __init__(self):
        # self.planes = [

        #     # Obj3D(
        #     #     position = [6, -5, 4],
        #     #     eulers = [-90, 0, 0]
        #     # ),
        #     # Obj3D(
        #     #     position = [6, 0, 0],
        #     #     eulers = [0, 0, 0]
        #     # ),
        #     # Obj3D(
        #     #     position = [6, -10, -30],
        #     #     eulers = [-90, 0, 0]
        #     # ),
        #     # Obj3D(
        #     #     position = [6, 40, -30],
        #     #     eulers = [-90, 0, 0]
        #     # ),
        # ]

        self.cubes = [
            Obj3D(
                position = [6, -5, 0],
                eulers = [0, 0, 0]
            ),
        #     Obj3D(
        #         position = [18, -3, 0],
        #         eulers = [0, 0, 0]
        #     ),
        #     Obj3D(
        #         position = [-20, 0, 0],
        #         eulers = [0, 0, 0]
        #     ),
        #     # Obj3D(
        #     #     position = [0, -3, -4],
        #     #     eulers = [0, 0, 0]
        #     # ),
        #     # Obj3D(
        #     #     position = [7, -3, 7],
        #     #     eulers = [0, 0, 0]
        #     # ),
        #     # Obj3D(
        #     #     position = [16, 10, 10],
        #     #     eulers = [1, 0, 0]
        #     # ),
        #     # Obj3D(
        #     #     position = [10, -13, -140],
        #     #     eulers = [-90, 0, 0]
        #     # ),
        #     # Obj3D(
        #     #     position = [17, -13, -30],
        #     #     eulers = [0, 0, 1]
        #     # )
        ]

        self.lights = [
            Light(
                position=[26, 4, -23],
                color=[1, 0, 0],
                strength=20
            ),
            Light(
                position=[20, 10, -25],
                color=[0, 1, 0],
                strength=10
            ),
            Light(
                position=[21, 14, -21],
                color=[1, 12, 10],
                strength=12
            ),
            Light(
                position=[20, 10, 0],
                color=[0, 0, 5],
                strength=0
            ),
            Light(
                position=[2, 5, 2],
                color=[1, 1, 0],
                strength=0
            ),
            Light(
                position=[-10, 10, 0],
                color=[0, 1, 0],
                strength=0
            ),
            Light(
                position=[16, 14, 13],
                color=[1, 12, 0],
                strength=0
            ),
            Light(
                position=[-10, 10, 0],
                color=[0, 1, 0],
                strength=0
            )
        ]

        # self.light_objects = [
        #     LightObj(self.lights[i], eulers=[0, 0, 0]) for i in range(5)
        # ]


        # self.floor = Obj3D(
        #         position = [-20, -20, -20],
        #         eulers = [-90, 0, 0]
        #         )
        
        # self.carpet = Obj3D(
        #     position = [-10, -20, -20],
        #     eulers = [0, 0, 0]
        # )

        self.entities: dict[int, list[Obj3D]] = {
            ENTITY_TYPE["CARPET"]: [
                Obj3D(
                    position = [-10, -20, -20],
                    eulers = [0, 0, 0]
                )
            ],

            ENTITY_TYPE["CUBE"]: [
                Obj3D(
                 position = [0, 0, 0],
                 eulers = [0, 0, 0]
                ),
                Obj3D(
                    position = [18, -3, 0],
                    eulers = [0, 0, 0]
                ),
                Obj3D(
                    position = [-20, 0, 0],
                    eulers = [0, 0, 0]
                ),
            ],

            ENTITY_TYPE["GLASS"]: [
                Obj3D(
                position = [-20, -20, -20],
                eulers = [-90, 0, 0]
                ),
                Obj3D(
                position = [0, 0, -20],
                eulers = [0, 0, 0]
                )
            ],
            ENTITY_TYPE["FLOOR"]: [
                Obj3D(
                position = [-20, -20, -20],
                eulers = [0, 0, 0]
                ),
                Obj3D(
                position = [20, -20, -20],
                eulers = [-90, -90, 0]
                )
            ],

            # ENTITY_TYPE["POINTLIGHT"]: [
            #     LightObj(self.lights[i], eulers=[0, 0, 0]) for i in range(5)
            # ]
        }

        self.camera = Camera(position=[0, 3, 12])

    def update(self, rate):
        for cube in self.cubes:
            cube.eulers[0] += 0.25 * rate
            cube.eulers[1] += 0.25 * rate
            cube.eulers[2] += 0.25 * rate
            if cube.eulers[0] > 360:
                cube.eulers[0] -= 360
            if cube.eulers[1] > 360:
                cube.eulers[1] -= 360
            if cube.eulers[2] > 360:
                cube.eulers[2] -= 360

    def move_camera(self, dPos):
        dPos = np.array(dPos, dtype = np.float32)
        self.camera.position += dPos
    
    def spin_camera(self, dPhi, dTheta):
        #self.camera.theta = (self.camera.theta + dTheta) % 360
        self.camera.theta = min(89, max(-89, self.camera.theta + dTheta))
        self.camera.phi = (self.camera.phi - dPhi) % 360
        #self.camera.phi = min(89, max(-89, self.camera.phi + dPhi))

        self.camera.update()

#объект сцены
class Obj3D:
    def __init__(self, position, eulers):
        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)

    def getModelTransform(self):
        model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
        #вращение
        model_transform = pyrr.matrix44.multiply(
            m1 = model_transform, 
            m2 = pyrr.matrix44.create_from_eulers(
                eulers=np.radians(self.eulers), dtype=np.float32
            )
        )
        #передвижение
        return pyrr.matrix44.multiply(
            m1 = model_transform, 
            m2 = pyrr.matrix44.create_from_translation(
                vec=np.array(self.position), dtype=np.float32
            )
        )

#свет
class Light:
    def __init__(self, position, color, strength):
        self.position = np.array(position, dtype=np.float32)
        self.color = np.array(color, dtype=np.float32)
        self.strength = strength

#источник света
class LightObj(Obj3D):
    def __init__(self, light, eulers):
        self.light = Light(light.position, light.color, light.strength)
        self.position = light.position
        self.eulers = eulers


class GraphicsEngine:
    def __init__(self):
        #инициализация opengl
        glClearColor(0.1, 0.2, 0.2, 1)  #цвет фона/очистки

        glEnable(GL_DEPTH_TEST)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        #glEnable(GL_CULL_FACE)
        #glCullFace(GL_BACK)


        self.meshes: dict[int, Mesh] = {
            ENTITY_TYPE["CARPET"]: ObjMesh("models/carpet.obj"),
            ENTITY_TYPE["POINTLIGHT"]: ObjMesh("models/cube.obj"),
            ENTITY_TYPE["CUBE"]: ObjMesh("models/cube.obj"),
            ENTITY_TYPE["GLASS"]: ObjMesh("models/glass.obj"),
            ENTITY_TYPE["FLOOR"]: PlaneMesh(40, 40, 1),
        }

        mt = Material3D("Carpet", "jpg")

        self.materials: dict[int, Material] = {
            ENTITY_TYPE["CARPET"]: mt,
            ENTITY_TYPE["CUBE"]: mt,
            ENTITY_TYPE["GLASS"]: mt,
            ENTITY_TYPE["POINTLIGHT"]: mt,
            ENTITY_TYPE["FLOOR"]: mt,
        }

        self.storageBuffers: dict[int, Buffer] = {
            ENTITY_TYPE["CARPET"]: Buffer(
                size = 1024, binding = 0,
                element_count = 16, dtype = np.float32
            ),
            ENTITY_TYPE["CUBE"]: Buffer(
                size = 1024, binding = 1,
                element_count = 16, dtype = np.float32
            ),
            ENTITY_TYPE["GLASS"]: Buffer(
                size = 1024, binding = 2,
                element_count = 16, dtype = np.float32
            ),
            ENTITY_TYPE["POINTLIGHT"]: Buffer(
                size = 1024, binding = 3,
                element_count = 16, dtype = np.float32
            ),
            ENTITY_TYPE["FLOOR"]: Buffer(
                size = 1024, binding = 4,
                element_count = 16, dtype = np.float32
            ),
        }

        self.shaders: dict[int, Shader] = {
            0: Shader("vertex.txt", "fragment.txt"),
            1: Shader("vertex_light.txt", "fragment_light.txt"),
        }

        self.setOnetimeUnifs()
        self.getUnifsLocs()

        # self.wood_texture = Material("gfx/wood.png")
        # self.floor_texture = Material("gfx/floor.jpeg")
        # self.cat_texture = Material("gfx/cat.png")
        # self.carpet_texture = Material("gfx/Carpet_COL.jpg")
        # self.cube_mesh = Mesh("models/glass.obj")
        # self.carpet_mesh = Mesh("models/carpet.obj")
        # self.plane_mesh = Plane(10, 10, 1)
        # self.floor_mesh = Plane(400, 400, 50)


        #создание шейдера
        # shader = self.createShader("shaders/vertex.txt", "shaders/fragment.txt")
        # self.rendererObj = Renderer(self.shaders[0])


        # self.light_mesh = Mesh("models/cube.obj")

        # shader = self.createShader("shaders/vertex_light.txt", "shaders/fragment_light.txt")
        # self.rendererLight = RendererLight(self.shaders[1])
    
    def setOnetimeUnifs(self):

        projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy = 45, aspect = SCREEN_WIDTH / SCREEN_HEIGHT,
            near = 0.1, far = 1000, dtype=np.float32
        )

        shader = self.shaders[0]
        shader.use()

        glUniformMatrix4fv(
            glGetUniformLocation(shader.prog,"projection"),
            1, GL_FALSE, projection_transform
        )

        glUniform3fv(
            glGetUniformLocation(shader.prog,"ambient"), 
            1, np.array([0.1, 0.1, 0.1],dtype=np.float32))

        glUniform1i(
            glGetUniformLocation(shader.prog, "material.albedo"), 0)

        glUniform1i(
            glGetUniformLocation(shader.prog, "material.ao"), 1)

        glUniform1i(
            glGetUniformLocation(shader.prog, "material.normal"), 2)

        glUniform1i(
            glGetUniformLocation(shader.prog, "material.specular"), 3)
        
        shader = self.shaders[1]
        shader.use()

        glUniformMatrix4fv(
            glGetUniformLocation(shader.prog,"projection"),
            1, GL_FALSE, projection_transform
        )

    def getUnifsLocs(self):
        shader = self.shaders[0]
        shader.use()

        shader.cacheSingleLoc(UNIFORM_TYPE["VIEW"], "view")
        shader.cacheSingleLoc(UNIFORM_TYPE["CAMERA_POS"], "cameraPos")
        shader.cacheSingleLoc(UNIFORM_TYPE["MODEL"], "model")

        for i in range(8):
            shader.cacheMultiLoc(UNIFORM_TYPE["LIGHT_COLOR"], f"Lights[{i}].color")
            shader.cacheMultiLoc(UNIFORM_TYPE["LIGHT_POS"], f"lightPos[{i}].position")
            shader.cacheMultiLoc(UNIFORM_TYPE["LIGHT_STRENGTH"], f"Lights[{i}].strength")

        shader = self.shaders[1]
        shader.use()

        shader.cacheSingleLoc(UNIFORM_TYPE["MODEL"], "model")
        shader.cacheSingleLoc(UNIFORM_TYPE["VIEW"], "view")
        shader.cacheSingleLoc(UNIFORM_TYPE["TINT"], "color")

    def render(self, scene):
        for entityType, entities in scene.entities.items():
            if entityType not in self.storageBuffers:
                continue
            
            storage_buffer = self.storageBuffers[entityType]
            for i, entity in enumerate(entities):
                model = entity.getModelTransform().reshape(16)
                storage_buffer.recordElem(i, model)

                #glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, model)  
                #glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, model_transform)
                #glDrawArrays(GL_TRIANGLES, 0, self.floor_mesh.vertex_count)
                #glUniformMatrix4fv(entity.getModelTransform(), 1, GL_FALSE, model_transform)

        #обновление экрана
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)    #очистка экрана

        view_transform = pyrr.matrix44.create_look_at(
            eye = scene.camera.position, 
            target = scene.camera.position + scene.camera.forwards,
            up = scene.camera.up, dtype=np.float32)

        shader = self.shaders[0]
        shader.use()

        glUniformMatrix4fv(shader.fetchSingleLoc(UNIFORM_TYPE["VIEW"]), 1, GL_FALSE, view_transform)
        glUniform3fv(shader.fetchSingleLoc(UNIFORM_TYPE["CAMERA_POS"]), 1, scene.camera.position)     

        for i, light in enumerate(scene.lights):
            glUniform3fv(shader.fetchMultiLoc(UNIFORM_TYPE["LIGHT_POS"], i), 1, light.position)
            glUniform3fv(shader.fetchMultiLoc(UNIFORM_TYPE["LIGHT_COLOR"], i), 1, light.color)
            glUniform1f(shader.fetchMultiLoc(UNIFORM_TYPE["LIGHT_STRENGTH"], i), light.strength)

        for entityType, entities in scene.entities.items():

            # if entityType not in self.storageBuffers:
            #     continue

            # self.storageBuffers[entityType].readFrom()


            
            self.materials[entityType].use()
            
            for entity in entities:
                model = entity.getModelTransform()
                glUniformMatrix4fv(shader.fetchSingleLoc(UNIFORM_TYPE["MODEL"]), 1, GL_FALSE, model)  
                self.meshes[entityType].draw()
            ##self.meshes[entityType].drawInstanced(0, len(entities))


        # shader = self.shaders[1]
        # shader.use()

        # glUniformMatrix4fv(shader.fetchSingleLoc(UNIFORM_TYPE["VIEW"]), 1, GL_FALSE, view_transform)

        # mesh = self.meshes[ENTITY_TYPE["POINTLIGHT"]]
        # glBindVertexArray(mesh.vao)


        # self.rendererObj.render(scene, self)
        # self.rendererLight.render(scene, self)

        glFlush()


        # glUseProgram(self.shader)

        # view_transform = pyrr.matrix44.create_look_at(
        #     eye = scene.camera.position, 
        #     target = scene.camera.position + scene.camera.forwards,
        #     up = scene.camera.up, dtype=np.float32)
        
        # glUniformMatrix4fv(self.viewMatrixLocation, 1, GL_FALSE, view_transform)

        # for i, light in enumerate(scene.lights):
        #     glUniform3fv(self.lightLocation["position"][i], 1, light.position)
        #     glUniform3fv(self.lightLocation["color"][i], 1, light.color)
        #     glUniform1f(self.lightLocation["strength"][i], light.strength)
        # glUniform3fv(self.cameraPosLoc, 1, scene.camera.position)


        # self.floor_texture.use()
        # glBindVertexArray(self.floor_mesh.vao)

        # model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
        # #вращение
        # model_transform = pyrr.matrix44.multiply(
        #     m1 = model_transform, 
        #     m2 = pyrr.matrix44.create_from_eulers(
        #         eulers=np.radians(scene.floor.eulers), dtype=np.float32
        #     )
        # )
        # #передвижение
        # model_transform = pyrr.matrix44.multiply(
        #     m1 = model_transform, 
        #     m2 = pyrr.matrix44.create_from_translation(
        #         vec=np.array(scene.floor.position), dtype=np.float32
        #     )
        # )
        # glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, model_transform)
        # glDrawArrays(GL_TRIANGLES, 0, self.floor_mesh.vertex_count)

        # self.wood_texture.use()
        # glBindVertexArray(self.cube_mesh.vao)

        # for cube in scene.cubes:
        #     model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
        #     #вращение
        #     model_transform = pyrr.matrix44.multiply(
        #         m1 = model_transform, 
        #         m2 = pyrr.matrix44.create_from_eulers(
        #             eulers=np.radians(cube.eulers), dtype=np.float32
        #         )
        #     )
        #     #передвижение
        #     model_transform = pyrr.matrix44.multiply(
        #         m1 = model_transform, 
        #         m2 = pyrr.matrix44.create_from_translation(
        #             vec=np.array(cube.position), dtype=np.float32
        #         )
        #     )
        #     glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, model_transform)
        #     glDrawArrays(GL_TRIANGLES, 0, self.cube_mesh.vertex_count)

        # self.cat_texture.use()
        # glBindVertexArray(self.plane_mesh.vao)

        # for plane in scene.planes:
        #     model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
        #     #вращение
        #     model_transform = pyrr.matrix44.multiply(
        #         m1 = model_transform, 
        #         m2 = pyrr.matrix44.create_from_eulers(
        #             eulers=np.radians(plane.eulers), dtype=np.float32
        #         )
        #     )
        #     #передвижение
        #     model_transform = pyrr.matrix44.multiply(
        #         m1 = model_transform, 
        #         m2 = pyrr.matrix44.create_from_translation(
        #             vec=np.array(plane.position), dtype=np.float32
        #         )
        #     )
        #     glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, model_transform)
        #     glDrawArrays(GL_TRIANGLES, 0, self.plane_mesh.vertex_count)



        # glFlush()

    def quit(self):
        for mesh in self.meshes.values():
            mesh.destroy()
        
        for material in self.materials.values():
            material.destroy()

        for shader in self.shaders.values():
            shader.destroy()

        for buffer in self.storageBuffers.values():
            buffer.destroy()

class Shader:
    def __init__(self, vertexFilepath, fragmentFilepath):
        self.prog = self.createShader(vertexFilepath, fragmentFilepath)
        self.singleUnifs: dict[int, int] = {}
        self.multiUnifs: dict[int, list[int]] = {}

    #создание и компиляция программ шейдеров
    def createShader(self, vertexFilepath, fragmentFilepath):
        with open(f"shaders/{vertexFilepath}", 'r') as f:
            vertex_src = f.readlines()

        with open(f"shaders/{fragmentFilepath}", 'r') as f:
            fragment_src = f.readlines()

        shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER), compileShader(fragment_src, GL_FRAGMENT_SHADER))

        #возврат дескриптора программы шейдера
        return shader

    #поиск и сохранение местоположения юниформы
    def cacheSingleLoc(self, unifType, unifName):
        self.singleUnifs[unifType] = glGetUniformLocation(self.prog, unifName)

    def cacheMultiLoc(self, unifType, unifName):
        if unifType not in self.multiUnifs:
            self.multiUnifs[unifType] = []
        
        self.multiUnifs[unifType].append(glGetUniformLocation(self.prog, unifName))

    #возврат положения юниформы
    def fetchSingleLoc(self, unifType):
        return self.singleUnifs[unifType]
    
    def fetchMultiLoc(self, unifType, index):
        return self.multiUnifs[unifType][index]
    
    def use(self):
        glUseProgram(self.prog)
    
    def destroy(self):
        glDeleteProgram(self.prog)

class Buffer:
    def __init__(self, size, binding, element_count, dtype):
        self.size = size
        self.binding = binding
        self.element_count = element_count
        self.dtype = dtype

        self.hostMem = np.zeros(element_count * size, dtype = dtype)
        self.deviceMem = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.deviceMem)
        glBufferData(GL_ARRAY_BUFFER, self.hostMem.nbytes, 
            self.hostMem, GL_STATIC_DRAW)
        
        # glEnableVertexAttribArray(5)
        # glVertexAttribPointer(5, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(0))
        # glEnableVertexAttribArray(6)
        # glVertexAttribPointer(6, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(16))
        # glEnableVertexAttribArray(5)
        # glVertexAttribPointer(7, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(32))
        # glEnableVertexAttribArray(5)
        # glVertexAttribPointer(8, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(48))
        # glVertexAttribDivisor(5, 1)
        # glVertexAttribDivisor(6, 1)
        # glVertexAttribDivisor(7, 1)
        # glVertexAttribDivisor(8, 1)
        # glBindBufferBase(GL_SHADER_STORAGE_BUFFER, binding, self.deviceMem)
        self.elements_updated = 0

    def recordElem(self, i, element):
        if i >= self.size:
            self.resize()

        index = self.element_count * i
        self.hostMem[index : index + self.element_count] = element[:]
        self.elements_updated += 1

    def resize(self):
        self.destroy()

        new_size = self.size * 2

        hostMem = np.zeros(self.element_count * new_size, dtype=self.dtype)
        hostMem[0:self.element_count * self.size] = self.hostMem[:]
        self.hostMem = hostMem
        self.size = new_size

        self.deviceMem = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.deviceMem)
        glBufferData(GL_ARRAY_BUFFER, self.hostMem.nbytes, 
            self.hostMem, GL_STATIC_DRAW)
        # glBufferStorage(
        #     GL_SHADER_STORAGE_BUFFER, self.hostMem.nbytes, 
        #     self.hostMem, GL_DYNAMIC_STORAGE_BIT)

    def readFrom(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.deviceMem)
        glBufferData(GL_ARRAY_BUFFER, self.hostMem.nbytes, 
            self.hostMem, GL_STATIC_DRAW)
        
        # glBufferSubData(GL_ARRAY_BUFFER, 0, self.element_count * 4 * self.elements_updated, self.hostMem)
        # glBindBufferBase(GL_ARRAY_BUFFER, self.binding, self.deviceMem)
        self.elements_updated = 0

    def destroy(self):
        glDeleteBuffers(1, (self.deviceMem,))

class Mesh:
    def __init__(self):
        #x, y, z, s, t, nx, ny, nz, tangent, bitangent
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

    def draw(self):
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)

    def drawInstanced(self, baseInst, instCount):
        # glBindVertexArray(self.vao)
        # glDrawArraysInstancedBaseInstance(GL_TRIANGLES, 0, self.vertex_count, instCount, baseInst)
        glBindVertexArray(self.vao)
        glDrawArraysInstanced(GL_TRIANGLES, 0, self.vertex_count, instCount)

    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))

class PlaneMesh(Mesh):
    def __init__(self, w, h, k):
        super().__init__()

        #вершины - x, y, z, s, t, normal, tangent, bitangent
        vertices = (
            -w/2, h/2, 0, 0, 0, 0, 0, -1, 
            -w/2, -h/2, 0, 0, k, 0, 0, -1,
            w/2, -h/2, 0, k, k, 0, 0, -1,
            -w/2, h/2, 0, 0, 0, 0, 0, -1,
            w/2, -h/2, 0, k, k, 0, 0, -1,
            w/2, h/2, 0, k, 0, 0, 0, -1,
        )

        self.vertex_count = len(vertices) // 8

        self.vertices = []
        t = b = 0
        for i in range(self.vertex_count):
            k = i * 8
            if i % 3 == 0:
                (t, b) = self.get_face_orientation(
                    [[vertices[j] for j in range(k, k + 3)], [vertices[j] for j in range(k + 3, k + 5)]],
                    [[vertices[j] for j in range(k + 8, k + 11)], [vertices[j] for j in range(k + 11, k + 13)]],
                    [[vertices[j] for j in range(k + 16, k + 19)], [vertices[j] for j in range(k + 19, k + 21)]])
            for j in range(8):
                self.vertices.append(vertices[k + j])

            for element in t:
                self.vertices.append(element)

            for element in b:
                self.vertices.append(element)

        self.vertices = np.array(self.vertices, dtype=np.float32)   #тип важен для правильного распознавания OpenGl

        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        #атрибут 0 - позиция
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(0))
        #0 - номер атрибута
        #3 - количество точек
        #тип значения
        #нужна ли нормализация значений
        #количество байт для перехода к след. значению
        #смещение

        #атрибут 1 - цвет
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(12))

        #нормаль
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(20))

        #тангент
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(32))

        #битангент
        glEnableVertexAttribArray(4)
        glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(44))

    def get_face_orientation(self, a, b, c):
        
        pos1 = np.array(a[0], dtype=np.float32)
        uv1 = np.array(a[1], dtype=np.float32)

        pos2 = np.array(b[0], dtype=np.float32)
        uv2 = np.array(b[1], dtype=np.float32)

        pos3 = np.array(c[0], dtype=np.float32)
        uv3 = np.array(c[1], dtype=np.float32)

        dPos1 = pos2 - pos1
        dPos2 = pos3 - pos1
        dUV1 = uv2 - uv1
        dUV2 = uv3 - uv1

        den = 1 / (dUV1[0] * dUV2[1] - dUV2[0] * dUV1[1])
        tangent = [den * (dUV2[1] * dPos1[i] - dUV1[1] * dPos2[i]) for i in range(3)]
        bitangent = [den * (-dUV2[0] * dPos1[i] + dUV1[0] * dPos2[i]) for i in range(3)]

        return (tangent, bitangent)

class ObjMesh(Mesh):
    def __init__(self, filename):
        super().__init__()

        #x, y, z, s, t, nx, ny, nz, tangent, bitangent
        self.vertices = self.loadMesh(filename)
        self.vertex_count = len(self.vertices) // 14
        self.vertices = np.array(self.vertices, dtype=np.float32)

        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        #расположение
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(0))

        #текстура
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(12))

        #нормаль
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(20))

        #тангент
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(32))

        #битангент
        glEnableVertexAttribArray(4)
        glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(44))

    #загрузка меша (сетки) из obj файла
    def loadMesh(self, filename):
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
    
    #чтение вершины
    def read_vertex_data(self, words):
        return [
            float(words[1]),
            float(words[2]),
            float(words[3])
        ]
    
    #чтение координат текстуры
    def read_texcoord_data(self, words):
        return [
            float(words[1]),
            float(words[2])
        ]

    #чтение векторов нормали
    def read_normal_data(self, words):
        return [
            float(words[1]),
            float(words[2]),
            float(words[3])
        ]

    #создание граней
    def read_face_data(self, words, v, vt, vn, vertices):
        
        triangleCount = len(words) - 3

        for i in range(triangleCount):
            tangent, bitangent = self.get_face_orientation(words, 1, 2 + i, 3 + i, v, vt)

            self.make_corner(words[1], v, vt, vn, vertices, tangent, bitangent)
            self.make_corner(words[2 + i], v, vt, vn, vertices, tangent, bitangent)
            self.make_corner(words[3 + i], v, vt, vn, vertices, tangent, bitangent)

    def get_face_orientation(self, words, a, b, c, v, vt):
        v_vt_vn = words[a].split("/")
        pos1 = np.array(v[int(v_vt_vn[0]) - 1], dtype=np.float32)
        uv1 = np.array(vt[int(v_vt_vn[1]) - 1], dtype=np.float32)

        v_vt_vn = words[b].split("/")
        pos2 = np.array(v[int(v_vt_vn[0]) - 1], dtype=np.float32)
        uv2 = np.array(vt[int(v_vt_vn[1]) - 1], dtype=np.float32)

        v_vt_vn = words[c].split("/")
        pos3 = np.array(v[int(v_vt_vn[0]) - 1], dtype=np.float32)
        uv3 = np.array(vt[int(v_vt_vn[1]) - 1], dtype=np.float32)

        dPos1 = pos2 - pos1
        dPos2 = pos3 - pos1
        dUV1 = uv2 - uv1
        dUV2 = uv3 - uv1

        den = 1 / (dUV1[0] * dUV2[1] - dUV2[0] * dUV1[1])
        tangent = [den * (dUV2[1] * dPos1[i] - dUV1[1] * dPos2[i]) for i in range(3)]
        bitangent = [den * (-dUV2[0] * dPos1[i] + dUV1[0] * dPos2[i]) for i in range(3)]

        return (tangent, bitangent)

    #запись описания вершины
    def make_corner(self, corner_description, v, vt, vn, vertices, tangent, bitangent):
        v_vt_vn = corner_description.split("/")
        if (v_vt_vn[0] != '\n'):
            for element in v[int(v_vt_vn[0]) - 1]:
                vertices.append(element)

            for element in vt[int(v_vt_vn[1]) - 1]:
                vertices.append(element)

            for element in vn[int(v_vt_vn[2]) - 1]:
                vertices.append(element)

            for element in tangent:
                vertices.append(element)

            for element in bitangent:
                vertices.append(element)

    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))

class Material:
    def __init__(self, unit, textureType):
        self.texture = glGenTextures(1)
        self.unit = unit
        self.textureType = textureType

        glBindTexture(textureType, self.texture)
        glTexParameteri(textureType, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(textureType, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(textureType, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        glTexParameteri(textureType, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    def use(self):
        glActiveTexture(GL_TEXTURE0 + self.unit)
        glBindTexture(self.textureType, self.texture)

    def destroy(self):
        glDeleteTextures(1, (self.texture,))

class Material2D(Material):
    def __init__(self, filepath, unit):
        super().__init__(unit, textureType = GL_TEXTURE_2D)
        with Image.open(filepath, mode = 'r') as img:
            img_width, img_height = img.size
            img = img.convert("RGBA")
            img_data = bytes(img.tobytes())
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img_width, img_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        glGenerateMipmap(GL_TEXTURE_2D)

#материал - из нескольких текстур
class Material3D(Material):
    def __init__(self, filename, filetype):
        self.textures: list[Material2D] = [
            Material2D(f"gfx/{filename}/{filename}_COL.{filetype}", 0),
            Material2D(f"gfx/{filename}/{filename}_AO.{filetype}", 1),
            Material2D(f"gfx/{filename}/{filename}_NRM.png", 2),
            Material2D(f"gfx/{filename}/{filename}_GLOSS.{filetype}", 3),
        ]

        # self.textures = []

        # #albedo: 0
        # self.textures.append(glGenTextures(1))
        # glBindTexture(GL_TEXTURE_2D, self.textures[0])
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # with Image.open(f"gfx/{filepath}_COL.{filetype}", mode = 'r') as image:
        #     image_width, image_height = image.size
        #     image = image.convert("RGBA")
        #     img_data = bytes(image.tobytes())
        #     glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image_width, image_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        # glGenerateMipmap(GL_TEXTURE_2D)

        # #ambient occlusion: 1
        # self.textures.append(glGenTextures(1))
        # glBindTexture(GL_TEXTURE_2D, self.textures[1])
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # with Image.open(f"gfx/{filepath}_AO.{filetype}", mode = 'r') as image:
        #     image_width, image_height = image.size
        #     image = image.convert("RGBA")
        #     img_data = bytes(image.tobytes())
        #     glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image_width, image_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        # glGenerateMipmap(GL_TEXTURE_2D)

        # #normal: 2
        # self.textures.append(glGenTextures(1))
        # glBindTexture(GL_TEXTURE_2D, self.textures[2])
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # with Image.open(f"gfx/{filepath}_NRM.{filetype}", mode = 'r') as image:
        #     image_width, image_height = image.size
        #     image = image.convert("RGBA")
        #     img_data = bytes(image.tobytes())
        #     glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image_width, image_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        # glGenerateMipmap(GL_TEXTURE_2D)

        # #specular: 3
        # self.textures.append(glGenTextures(1))
        # glBindTexture(GL_TEXTURE_2D, self.textures[3])
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # with Image.open(f"gfx/{filepath}_GLOSS.{filetype}", mode = 'r') as image:
        #     image_width, image_height = image.size
        #     image = image.convert("RGBA")
        #     img_data = bytes(image.tobytes())
        #     glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image_width, image_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        # glGenerateMipmap(GL_TEXTURE_2D)

    def use(self):
        for texture in self.textures:
            texture.use()

        # for i in range(len(self.textures)):
        #     glActiveTexture(GL_TEXTURE0 + i)
        #     glBindTexture(GL_TEXTURE_2D, self.textures[i])

    def destroy(self):
        for texture in self.textures:
            texture.destroy()

        # glDeleteTextures(len(self.textures), self.textures)

class Plane:
    def __init__(self, w, h, k):

        #вершины - x, y, z, s, t, normal
        self.vertices = (
            -w/2, h/2, 0, 0, 0, 0, 0, -1,
            -w/2, -h/2, 0, 0, k, 0, 0, -1,
            w/2, -h/2, 0, k, k, 0, 0, -1,
            -w/2, h/2, 0, 0, 0, 0, 0, -1,
            w/2, -h/2, 0, k, k, 0, 0, -1,
            w/2, h/2, 0, k, 0, 0, 0, -1,
        )


        self.vertex_count = len(self.vertices) // 8
        self.vertices = np.array(self.vertices, dtype=np.float32)   #тип важен для правильного распознавания OpenGl

        self.vao = glGenVertexArrays(1) #vertex array - массив вершин
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)  #буфер вершин
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        #атрибут 0 - позиция
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))
        #0 - номер атрибута
        #3 - количество точек
        #тип значения
        #нужна ли нормализация значений
        #количество байт для перехода к след. значению
        #смещение

        #атрибут 1 - цвет
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))


        #нормаль
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(20))

    #очистка памяти
    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))

if __name__ == "__main__":
    window = initialize_glfw()
    myApp = App(window)