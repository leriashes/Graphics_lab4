import pygame as pg
import glfw
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

        

        #создание объекта
        self.triangle = Triangle()

        #создание шейдера
        self.shader = self.createShader("shaders/vertex.txt", "shaders/fragment.txt")
        #glUseProgram(self.shader)

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
            glBindVertexArray(self.triangle.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.triangle.vertex_count)

            pg.display.flip()

            self.clock.tick(60)
        self.quit() #выход из приложения

    def quit(self):
        self.triangle.destroy()
        glDeleteProgram(self.shader)
        pg.quit()

class Triangle:
    def __init__(self):

        #вершины - x, y, z, r, g, b
        self.vertices = (
            -0.5, -0.5, 0.0, 1.0, 0.0, 0.0,
            0.5, -0.5, 0.0, 0.0, 1.0, 0.0,
            0.0, 0.5, 0.0, 0.0, 0.0, 1.0
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
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
        #0 - номер атрибута
        #3 - количество точек
        #тип значения
        #нужна ли нормализация значений
        #количество байт для перехода к след. значению
        #смещение

        #атрибут 1 - цвет
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))


    #очистка памяти
    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))

if __name__ == "__main__":

    myApp = App()