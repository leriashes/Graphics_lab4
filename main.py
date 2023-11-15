import pygame as pg
from OpenGL.GL import *
import numpy as np
from OpenGL.GL.shaders import compileProgram, compileShader

class App:

    def __init__(self):
        #инициализация pygame
        pg.init()

        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 4)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 1)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.set_mode((640, 480), pg.OPENGL|pg.DOUBLEBUF) #создание окна: размеры окна, использование opengl, двойная буфферизация - один буфер отрисовывается, в то время как второй виден на экране
        self.clock = pg.time.Clock()

        #инициализация opengl
        glClearColor(0.1, 0.2, 0.2, 1)  #цвет фона/очистки
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        

        #создание объекта
        self.triangle = Triangle()

        self.wood_texture = Material("gfx/cat.png")

        #создание шейдера
        self.shader = self.createShader("shaders/vertex.txt", "shaders/fragment.txt")
        
        glUseProgram(self.shader)
        glUniform1i(glGetUniformLocation(self.shader, "imageTexture"), 0)

        self.mainLoop()

    def createShader(self, vertexFilepath, fragmentFilepath):
        
        #glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE)
        #glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)

        with open(vertexFilepath, 'r') as f:
            vertex_src = f.readlines()

        with open(fragmentFilepath, 'r') as f:
            fragment_src = f.readlines()

        shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER), compileShader(fragment_src, GL_FRAGMENT_SHADER))

        return shader

    def mainLoop(self):
        running = True

        while(running):
            #проверка событий
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False

            #обновление экрана
            glClear(GL_COLOR_BUFFER_BIT)    #очистка экрана

            glUseProgram(self.shader)
            self.wood_texture.use()
            glBindVertexArray(self.triangle.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.triangle.vertex_count)

            pg.display.flip()

            self.clock.tick(60)
        self.quit() #выход из приложения

    def quit(self):
        self.triangle.destroy()
        self.wood_texture.destroy()
        glDeleteProgram(self.shader)
        pg.quit()

class Triangle:
    def __init__(self):

        #вершины - x, y, z, r, g, b, s, t
        self.vertices = (
            -0.5, -0.5, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0,
            0.5, -0.5, 0.0, 0.0, 1.0, 0.0, 1.0, 1.0,
            0.0, 0.5, 0.0, 0.0, 0.0, 1.0, 0.5, 0.0
        )

        self.vertices = np.array(self.vertices, dtype=np.float32)   #тип важен для правильного распознавания OpenGl

        self.vertex_count = 3

        self.vao = glGenVertexArrays(1) #vertex array - массив вершин
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)  #буфер вершин
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        #атрибут 0 - позиция
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))
        #0 - номер атрибута
        #3 - количество значений
        #тип значения
        #нужна ли нормализация значений
        #количество байт для перехода к след. значению
        #смещение

        #атрибут 1 - цвет
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))

        #атрибут 2 - позиция текстуры
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(24))


    #очистка памяти
    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))

class Cube:
    def __init__(self, shader, material, position):
        self.material = material
        self.shader = shader
        self.position = position

        glUseProgram(shader)

        #вершины - x, y, z, s, t, nx, ny, nz
        self.vertices = (
            -0.5, -0.5, -0.5, 0, 0, 0, 0, -1,
            0.5, -0.5, -0.5, 1, 0, 0, 0, -1,
            0.5, 0.5, -0.5, 1, 1, 0, 0, -1,

            0.5, 0.5, -0.5, 1, 1, 0, 0, -1,
            -0.5, 0.5, -0.5, 0, 1, 0, 0, -1,
            -0.5, -0.5, -0.5, 0, 0, 0, 0, -1,

            -0.5, -0.5, 0.5, 0, 0, 0, 0, 1,
            0.5, -0.5, 0.5, 1, 0, 0, 0, 1,
            0.5, 0.5, 0.5, 1, 1, 0, 0, 1,

            0.5, 0.5, 0.5, 1, 1, 0, 0, 1,
            -0.5, 0.5, 0.5, 0, 1, 0, 0, 1,
            -0.5, -0.5, 0.5, 0, 0, 0, 0, 1,

            -0.5, 0.5, 0.5, 1, 0, -1, 0, 0,
            -0.5, 0.5, -0.5, 1, 1, -1, 0, 0,
            -0.5, -0.5, -0.5, 0, 1, -1, 0, 0,

            -0.5, -0.5, -0.5, 0, 1, -1, 0, 0,
            -0.5, -0.5, 0.5, 0, 0, -1, 0, 0,
            -0.5, 0.5, 0.5, 1, 0, -1, 0, 0,

            0.5, 0.5, 0.5, 1, 0, 1, 0, 0,
            0.5, 0.5, -0.5, 1, 1, 1, 0, 0,
            0.5, -0.5, -0.5, 0, 1, 1, 0, 0,

            0.5, -0.5, -0.5, 0, 1, 1, 0, 0,
            0.5, -0.5, 0.5, 0, 0, 1, 0, 0,
            0.5, 0.5, 0.5, 1, 0, 1, 0, 0,

            -0.5, -0.5, -0.5, 0, 1, 0, -1, 0,
            0.5, -0.5, -0.5, 1, 1, 0, -1, 0,
            0.5, -0.5, 0.5, 1, 0, 0, -1, 0,

            0.5, -0.5, 0.5, 1, 0, 0, -1, 0,
            -0.5, -0.5, 0.5, 0, 0, 0, -1, 0,
            -0.5, -0.5, -0.5, 0, 1, 0, -1, 0,

            -0.5, 0.5, -0.5, 0, 1, 0, 1, 0,
            0.5, 0.5, -0.5, 1, 1, 0, 1, 0,
            0.5, 0.5, 0.5, 1, 0, 0, 1, 0,

            0.5, 0.5, 0.5, 1, 0, 0, 1, 0,
            -0.5, 0.5, 0.5, 0, 0, 0, 1, 0,
            -0.5, 0.5, -0.5, 0, 1, 0, 1, 0,
        )

        self.vertex_count = len(self.vertices) // 8
        self.vertices = np.array(self.vertices, dtype=np.float32)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        glEnableVertexArrayAttrib(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))

        glEnableVertexArrayAttrib(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))

        glEnableVertexArrayAttrib(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(20))

class Material:
    def __init__(self, filepath):
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        image = pg.image.load(filepath).convert_alpha()
        image_width, image_height = image.get_rect().size
        image_data = pg.image.tostring(image, "RGBA")

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image_width, image_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
        glGenerateMipmap(GL_TEXTURE_2D)

    def use(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture)

    def destroy(self):
        glDeleteTextures(1, (self.texture,))

if __name__ == "__main__":

    myApp = App()