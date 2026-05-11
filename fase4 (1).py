# ============================================================
#  SOFTWARE FJ — Sistema de Gestión de Clientes y Reservas
#  
# ============================================================

from abc import ABC, abstractmethod
from datetime import datetime
import logging

# Configuración del archivo de logs
logging.basicConfig(
    filename="logs.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ============================================================
# SECCIÓN 1: EXCEPCIONES PERSONALIZADAS


class ErrorSistema(Exception):
    """Error general del sistema. Padre de todas las excepciones propias."""
    pass

class ErrorValidacion(ErrorSistema):
    """Se lanza cuando un dato ingresado no cumple las reglas de negocio
    (nombre incompleto, email inválido, costo negativo, etc.)."""
    pass

class ErrorReserva(ErrorSistema):
    """Se lanza cuando falla la creación, procesamiento o estado de una reserva."""
    pass

class IndiceInvalido(ErrorSistema):
    """Se lanza cuando el usuario selecciona un índice fuera de rango en una lista."""
    pass

class ErrorServicio(ErrorSistema):
    """Se lanza cuando se intenta operar con un servicio no disponible o inválido."""
    pass


# ============================================================
# SECCIÓN 2: CLASE ABSTRACTA BASE — Entidad

# ============================================================

class Entidad(ABC):
    """Clase abstracta raíz. Define el contrato mínimo de toda entidad."""

    @abstractmethod
    def mostrar_info(self) -> str:
        """Retorna una descripción legible de la entidad."""
        pass



# 
#  Herencia, Encapsulación, Abstracción
#


class Cliente(Entidad):
    """Representa a un cliente registrado en el sistema.

    Atributos privados:
        __nombre  : Nombre completo (mínimo nombre y apellido).
        __email   : Correo electrónico con formato válido.
        __historial: Lista de reservas confirmadas del cliente.
    """

    def __init__(self, nombre: str, email: str):
       
        try:
            self.__nombre   = nombre.strip()
            self.__email    = email.strip()
            self.__historial = []          # ← CORRECCIÓN: inicializar siempre
            self.__validar()

        except ErrorValidacion as e:
            logging.error(f"Error al crear cliente '{nombre}': {e}")
            raise  # Relanzamos para que el llamador pueda manejarlo

        else:
            logging.info(f"Cliente creado exitosamente: {self.__nombre} — {self.__email}")

    # ── Validación interna ───────────────────────────────────
    def __validar(self):
        """Valida nombre (≥ 2 palabras) y formato de email."""
        partes = self.__nombre.split()
        if len(partes) < 2:
            raise ErrorValidacion(
                f"El nombre '{self.__nombre}' debe incluir nombre y apellido."
            )

        # Validación básica de email: debe tener '@' y un '.' después de '@'
        partes_email = self.__email.split("@")
        if len(partes_email) != 2 or "." not in partes_email[1]:
            raise ErrorValidacion(
                f"El email '{self.__email}' no tiene un formato válido."
            )

    # ── Métodos públicos ─────────────────────────────────────
    def agregar_al_historial(self, reserva) -> None:
        """Agrega una reserva confirmada al historial del cliente."""
        self.__historial.append(reserva)

    def ver_historial(self) -> list:
        """Retorna una copia del historial de reservas (encapsulación)."""
        return list(self.__historial)

    def mostrar_info(self) -> str:
        return f"{self.__nombre} — {self.__email}"

    def __str__(self) -> str:
        return self.mostrar_info()



# SECCIÓN 4: CLASE ABSTRACTA Servicio y sus derivadas



class Servicio(ABC):
    """Clase abstracta que representa cualquier servicio ofrecido por Software FJ.

    Atributos:
        nombre     : Nombre descriptivo del servicio.
        costo_base : Precio unitario base (por hora, día o sesión).
        disponible : Indica si el servicio puede reservarse actualmente.
    """

    def __init__(self, nombre: str, costo_base: float):
        if not nombre or not nombre.strip():
            raise ErrorValidacion("El nombre del servicio no puede estar vacío.")
        if costo_base < 0:
            raise ErrorValidacion(
                f"El costo base no puede ser negativo. Se recibió: {costo_base}."
            )

        self.nombre     = nombre.strip()
        self.costo_base = float(costo_base)
        self.disponible = True

    # ── Método abstracto (polimorfismo obligatorio) ──────────
    @abstractmethod
    def calcular_costo(self, cantidad: int, descuento: float = 0,
                       impuesto: float = 0) -> float:
        """Calcula el costo total según la duración y ajustes opcionales.
        Cada subclase define la lógica concreta (horas, días, sesiones).
        """
        pass

    @abstractmethod
    def mostrar_info(self) -> str:
        """Retorna descripción completa del servicio."""
        pass

    # ── Método compartido: aplica descuento e impuesto ───────
    def aplicar_ajustes(self, total: float, descuento: float = 0,
                        impuesto: float = 0) -> float:
        """Aplica descuento primero y luego impuesto sobre el subtotal.

        Sobrecarga simulada mediante parámetros opcionales:
          - Sin parámetros   → devuelve total sin cambios.
          - Con descuento    → aplica solo el descuento.
          - Con ambos        → descuento primero, luego impuesto.
        """
        total -= total * descuento   # Descuento sobre precio original
        total += total * impuesto    # Impuesto sobre precio descontado
        return round(total, 2)


# ────────────────────────────────────────────────────────────
# Servicio 1: ReservaSala
# Unidad de cobro: horas
# ────────────────────────────────────────────────────────────
class ReservaSala(Servicio):
    """Sala de reuniones o conferencias, cobro por hora."""

    def calcular_costo(self, horas: int, descuento: float = 0,
                       impuesto: float = 0) -> float:
        """
        Sobrecarga 1 (sin ajustes)  : calcular_costo(3)
        Sobrecarga 2 (con descuento): calcular_costo(3, descuento=0.10)
        Sobrecarga 3 (completo)     : calcular_costo(3, 0.10, 0.08)
        """
        if horas <= 0:
            raise ErrorValidacion("Las horas reservadas deben ser mayores a 0.")
        total = self.costo_base * horas
        return self.aplicar_ajustes(total, descuento, impuesto)

    def mostrar_info(self) -> str:
        estado = "Disponible" if self.disponible else "No disponible"
        return f"[Sala]    {self.nombre:<20} | ${self.costo_base:>10,.0f}/hora  | {estado}"


# ────────────────────────────────────────────────────────────
# Servicio 2: AlquilerEquipo
# Unidad de cobro: días
# ────────────────────────────────────────────────────────────
class AlquilerEquipo(Servicio):
    """Equipos tecnológicos (PC, proyector, sonido), cobro por día."""

    def calcular_costo(self, dias: int, descuento: float = 0,
                       impuesto: float = 0) -> float:
        """
        Sobrecarga 1 (sin ajustes)  : calcular_costo(5)
        Sobrecarga 2 (con descuento): calcular_costo(5, descuento=0.10)
        Sobrecarga 3 (completo)     : calcular_costo(5, 0.10, 0.08)
        """
        if dias <= 0:
            raise ErrorValidacion("Los días de alquiler deben ser mayores a 0.")
        total = self.costo_base * dias
        return self.aplicar_ajustes(total, descuento, impuesto)

    def mostrar_info(self) -> str:
        estado = "Disponible" if self.disponible else "No disponible"
        return f"[Equipo]  {self.nombre:<20} | ${self.costo_base:>10,.0f}/día   | {estado}"


# ────────────────────────────────────────────────────────────
# Servicio 3: Asesoria
# Unidad de cobro: sesiones
# Atributo adicional: asesor asignado
# ────────────────────────────────────────────────────────────
class Asesoria(Servicio):
    """Asesoría especializada (básica o avanzada), cobro por sesión."""

    def __init__(self, nombre: str, costo_base: float, asesor: str):
        super().__init__(nombre, costo_base)
        if not asesor or not asesor.strip():
            raise ErrorValidacion("El nombre del asesor no puede estar vacío.")
        self.asesor = asesor.strip()

    def calcular_costo(self, sesiones: int, descuento: float = 0,
                       impuesto: float = 0) -> float:
        """
        Sobrecarga 1 (sin ajustes)  : calcular_costo(2)
        Sobrecarga 2 (con descuento): calcular_costo(2, descuento=0.10)
        Sobrecarga 3 (completo)     : calcular_costo(2, 0.10, 0.08)
        """
        if sesiones <= 0:
            raise ErrorValidacion("El número de sesiones debe ser mayor a 0.")
        total = self.costo_base * sesiones
        return self.aplicar_ajustes(total, descuento, impuesto)

    def mostrar_info(self) -> str:
        estado = "Disponible" if self.disponible else "No disponible"
        return (f"[Asesoría] {self.nombre:<19} | ${self.costo_base:>10,.0f}/sesión"
                f" | Asesor: {self.asesor} | {estado}")


# SECCIÓN 5: CLASE Reserva


class Reserva:
    """Representa una reserva de servicio para un cliente.

    Estados posibles: 'pendiente', 'confirmada', 'cancelada'.
    """

    def __init__(self, cliente: Cliente, servicio: Servicio, duracion: int):
        # try/except/finally:
        #   try     → valida todos los parámetros y crea la reserva.
        #   except  → encadena el error en ErrorReserva (conserva causa).
        #   finally → SIEMPRE registra el intento en logs, haya fallo o no.
        try:
            if not isinstance(cliente, Cliente):
                raise ErrorValidacion("El parámetro 'cliente' no es una instancia válida.")
            if not isinstance(servicio, Servicio):
                raise ErrorValidacion("El parámetro 'servicio' no es una instancia válida.")
            if not servicio.disponible:
                raise ErrorServicio(
                    f"El servicio '{servicio.nombre}' no está disponible para reservas."
                )
            if duracion <= 0:
                raise ErrorValidacion("La duración debe ser un entero positivo mayor a 0.")

            self.cliente  = cliente
            self.servicio = servicio
            self.duracion = duracion
            self.estado   = "pendiente"
            self.fecha    = datetime.now()

        except (ErrorValidacion, ErrorServicio) as e:
            logging.error(f"Fallo al crear reserva para '{cliente}' — {servicio.nombre}: {e}")
         
            raise ErrorReserva(f"No se pudo crear la reserva: {e}") from e

        finally:
            # Este bloque se ejecuta SIEMPRE, incluso si se lanzó una excepción.
            logging.info(
                f"Intento de reserva | cliente='{cliente}' "
                f"| servicio='{servicio.nombre}' | duración={duracion}"
            )

    # ── Cambios de estado ────────────────────────────────────
    def confirmar(self) -> None:
        """Confirma la reserva y la agrega al historial del cliente."""
        self.estado = "confirmada"
        self.cliente.agregar_al_historial(self)
        logging.info(f"Reserva CONFIRMADA | {self.cliente} | {self.servicio.nombre}")

    def cancelar(self) -> None:
        """Cancela la reserva."""
        self.estado = "cancelada"
        logging.info(f"Reserva CANCELADA | {self.cliente} | {self.servicio.nombre}")

    # ── Procesamiento principal ──────────────────────────────
    def procesar(self, descuento: float = 0, impuesto: float = 0) -> str:
        """Calcula el costo y confirma la reserva si no hay errores.

        Estructura try/except/else:
          try   → intenta calcular el costo usando polimorfismo.
          except→ cancela la reserva y encadena el error.
          else  → solo confirma si el cálculo fue exitoso.

        Args:
            descuento: Fracción de descuento (0.0 – 1.0). Default 0.
            impuesto : Fracción de impuesto  (0.0 – 1.0). Default 0.

        Returns:
            Cadena con resumen de la reserva confirmada.

        Raises:
            ErrorReserva: Si el cálculo de costo falla por cualquier motivo.
        """
        try:
            cantidad = int(self.duracion)

            # POLIMORFISMO: cada subclase de Servicio implementa su propio
            # calcular_costo(), por lo que esta línea funciona igual para
            # ReservaSala, AlquilerEquipo y Asesoria sin if/elif.
            costo = self.servicio.calcular_costo(cantidad, descuento, impuesto)

            # Determinamos la unidad léxica correcta según el tipo de servicio
            if isinstance(self.servicio, ReservaSala):
                unidad = "hora" if cantidad == 1 else "horas"
            elif isinstance(self.servicio, AlquilerEquipo):
                unidad = "día"  if cantidad == 1 else "días"
            else:                                         # Asesoria
                unidad = "sesión" if cantidad == 1 else "sesiones"

        except Exception as e:
            self.cancelar()
            raise ErrorReserva("Error al procesar la reserva.") from e  # Encadenamiento

        else:
            # Solo se ejecuta si el bloque try terminó sin excepciones
            self.confirmar()
            desc_str = f" (desc. {descuento*100:.0f}%)" if descuento else ""
            imp_str  = f" (imp. {impuesto*100:.0f}%)"  if impuesto  else ""
            return (
                f"✔ Reserva confirmada | "
                f"Servicio: {self.servicio.nombre} | "
                f"Duración: {cantidad} {unidad} | "
                f"Costo: ${costo:,.0f}{desc_str}{imp_str}"
            )

    def __str__(self) -> str:
        return (
            f"Reserva [{self.estado.upper():<11}] | "
            f"{self.cliente.mostrar_info()} | "
            f"{self.servicio.nombre} | "
            f"Duración: {self.duracion} | "
            f"Fecha: {self.fecha.strftime('%Y-%m-%d %H:%M')}"
        )


# SECCIÓN 6: CLASE Sistema
# Gestiona las listas internas y el menú interactivo.


class Sistema:
    """Controlador principal. Mantiene las colecciones de clientes,
    servicios y reservas, y expone el menú de usuario."""

    def __init__(self):
        self.clientes  : list[Cliente]  = []
        self.servicios : list[Servicio] = []
        self.reservas  : list[Reserva]  = []

        # Catálogos predefinidos de nombres disponibles
        self.salas     = ["Sala A", "Sala B", "Sala VIP"]
        self.equipos   = ["PC Gamer", "Proyector 4K", "Sistema de Sonido"]
        self.asesorias = ["Asesoría Básica", "Asesoría Avanzada"]

    # ── Utilidad de validación de índice ────────────────────
    def validar_indice(self, lista: list, i: int) -> None:
        """Lanza IndiceInvalido si el índice está fuera del rango de la lista."""
        if i < 0 or i >= len(lista):
            raise IndiceInvalido(
                f"Índice {i} inválido. Rango permitido: 0 – {len(lista) - 1}."
            )

    # ── Registro de cliente ──────────────────────────────────
    def registrar_cliente(self) -> None:
        """Solicita datos por consola y registra un nuevo cliente.

        Estructura try/except/finally:
          try     → intenta crear y guardar el cliente.
          except  → muestra el error sin detener el sistema.
          finally → registra el intento en logs siempre.
        """
        try:
            nombre = input("  Nombre y apellido: ").strip()
            email  = input("  Email: ").strip()
            cliente = Cliente(nombre, email)
            self.clientes.append(cliente)
            print(f"  ✔ Cliente registrado: {cliente}")

        except ErrorValidacion as e:
            print(f"  ✗ Error de validación: {e}")

        except Exception as e:
            logging.error(f"Error inesperado al registrar cliente: {e}")
            print(f"  ✗ Error inesperado: {e}")

        finally:
            logging.info("Intento de registro de cliente finalizado.")

    # ── Creación de servicio ─────────────────────────────────
    def crear_servicio(self) -> None:
        """Solicita datos por consola y crea un nuevo servicio."""
        try:
            print("\n  Tipo de servicio:")
            print("  1. Sala de reuniones")
            print("  2. Alquiler de equipo")
            print("  3. Asesoría especializada")
            tipo = int(input("  Seleccione tipo (1-3): "))

            if tipo == 1:
                for i, s in enumerate(self.salas):
                    print(f"    {i} → {s}")
                idx  = int(input("  Seleccione sala: "))
                self.validar_indice(self.salas, idx)
                costo   = float(input("  Costo por hora ($): "))
                servicio = ReservaSala(self.salas[idx], costo)

            elif tipo == 2:
                for i, e in enumerate(self.equipos):
                    print(f"    {i} → {e}")
                idx  = int(input("  Seleccione equipo: "))
                self.validar_indice(self.equipos, idx)
                costo   = float(input("  Costo por día ($): "))
                servicio = AlquilerEquipo(self.equipos[idx], costo)

            elif tipo == 3:
                for i, a in enumerate(self.asesorias):
                    print(f"    {i} → {a}")
                idx   = int(input("  Seleccione asesoría: "))
                self.validar_indice(self.asesorias, idx)
                asesor  = input("  Nombre del asesor: ").strip()
                costo   = float(input("  Costo por sesión ($): "))
                servicio = Asesoria(self.asesorias[idx], costo, asesor)

            else:
                raise ErrorValidacion(f"Tipo '{tipo}' no es válido. Ingrese 1, 2 ó 3.")

            self.servicios.append(servicio)
            logging.info(f"Servicio creado: {servicio.nombre}")
            print(f"   Servicio creado: {servicio.mostrar_info()}")

        except (ErrorValidacion, IndiceInvalido) as e:
            print(f"  ✗ Error: {e}")

        except ValueError:
            print("  ✗ Entrada inválida. Por favor ingrese un número.")

        except Exception as e:
            logging.error(f"Error inesperado al crear servicio: {e}")
            print(f"  ✗ Error inesperado: {e}")

        finally:
            logging.info("Intento de creación de servicio finalizado.")

    # ── Listados ─────────────────────────────────────────────
    def ver_clientes(self) -> None:
        if not self.clientes:
            print("  (No hay clientes registrados)")
            return
        print()
        for i, c in enumerate(self.clientes):
            print(f"  {i} → {c.mostrar_info()}")

    def ver_servicios(self) -> None:
        if not self.servicios:
            print("  (No hay servicios creados)")
            return
        print()
        for i, s in enumerate(self.servicios):
            print(f"  {i} → {s.mostrar_info()}")

    def ver_reservas(self) -> None:
        if not self.reservas:
            print("  (No hay reservas registradas)")
            return
        print()
        for i, r in enumerate(self.reservas):
            print(f"  {i} → {r}")

    # ── Creación de reserva ──────────────────────────────────
    def crear_reserva(self) -> None:
        """Guía al usuario para crear y procesar una reserva."""
        try:
            print("\n  — Clientes disponibles —")
            self.ver_clientes()
            c = int(input("  Seleccione cliente (índice): "))
            self.validar_indice(self.clientes, c)

            print("\n  — Servicios disponibles —")
            self.ver_servicios()
            s = int(input("  Seleccione servicio (índice): "))
            self.validar_indice(self.servicios, s)

            duracion = int(input("  Duración (número entero positivo): "))

            desc = input("  ¿Aplicar descuento 10%? (si/no): ").strip().lower()
            descuento = 0.10 if desc == "si" else 0

            imp = input("  ¿Aplicar impuesto 8%? (si/no): ").strip().lower()
            impuesto = 0.08 if imp == "si" else 0

            reserva  = Reserva(self.clientes[c], self.servicios[s], duracion)
            resultado = reserva.procesar(descuento, impuesto)
            self.reservas.append(reserva)
            print(f"\n  {resultado}")

        except ErrorReserva as e:
            print(f"  ✗ Error en reserva: {e}")

        except (IndiceInvalido, ValueError) as e:
            print(f"  ✗ Error: {e}")

        except Exception as e:
            logging.error(f"Error inesperado en crear_reserva: {e}")
            print(f"  ✗ Error inesperado: {e}")

        finally:
            logging.info("Intento de creación de reserva finalizado.")

    # ── Menú principal ───────────────────────────────────────
    def menu(self) -> None:
        """Bucle principal del menú interactivo."""
        while True:
            print("\n" + "=" * 46)
            print("        SISTEMA SOFTWARE FJ — MENÚ")
            print("=" * 46)
            print("  1. Registrar cliente")
            print("  2. Crear servicio")
            print("  3. Ver clientes")
            print("  4. Ver servicios")
            print("  5. Crear reserva")
            print("  6. Ver reservas")
            print("  7. Salir")
            print("=" * 46)

            op = input("  Seleccione una opción: ").strip()

            if   op == "1": self.registrar_cliente()
            elif op == "2": self.crear_servicio()
            elif op == "3": self.ver_clientes()
            elif op == "4": self.ver_servicios()
            elif op == "5": self.crear_reserva()
            elif op == "6": self.ver_reservas()
            elif op == "7":
                print("  Hasta luego. ¡Gracias por usar Software FJ!")
                logging.info("Sistema cerrado por el usuario.")
                break
            else:
                print("  ✗ Opción inválida. Ingrese un número del 1 al 7.")


# SECCIÓN 7: SIMULACIÓN — 10 operaciones automáticas


def simulacion() -> "Sistema":
    """Ejecuta 10 operaciones automáticas para demostrar el sistema.

    Cubre:
      • Creación de clientes válidos e inválidos.
      • Creación de servicios válidos e inválidos.
      • Reservas exitosas con descuento e impuesto.
      • Reservas fallidas por duración 0, servicio inactivo.
      • Cancelación manual de una reserva confirmada.
      • Verificación del historial de un cliente.
    """
    SEP = "=" * 55

    print(f"\n{SEP}")
    print("   SIMULACIÓN AUTOMÁTICA — 10 OPERACIONES")
    print(SEP)

    sistema = Sistema()

    # ----------------------------------------------------------
    # OP 1 — Cliente válido
    # ----------------------------------------------------------
    print("\n[OP 1] Registrar cliente válido")
    try:
        c1 = Cliente("Juan Pérez", "juan@correo.com")
        sistema.clientes.append(c1)
        print(f"   Cliente creado: {c1}")
    except ErrorValidacion as e:
        print(f"  ✗ {e}")

    # ----------------------------------------------------------
    # OP 2 — Cliente con email inválido (error esperado)
    # ----------------------------------------------------------
    print("\n[OP 2] Registrar cliente con email inválido")
    try:
        c2 = Cliente("Ana Gómez", "correo-sin-arroba")
        sistema.clientes.append(c2)
    except ErrorValidacion as e:
        print(f"  ✗ Error esperado capturado: {e}")

    # ----------------------------------------------------------
    # OP 3 — Cliente sin apellido (error esperado)
    # ----------------------------------------------------------
    print("\n[OP 3] Registrar cliente sin apellido")
    try:
        c3 = Cliente("Pedro", "pedro@correo.com")
        sistema.clientes.append(c3)
    except ErrorValidacion as e:
        print(f"  ✗ Error esperado capturado: {e}")

    # ----------------------------------------------------------
    # OP 4 — Crear tres servicios válidos
    # ----------------------------------------------------------
    print("\n[OP 4] Crear servicios válidos (sala, equipo, asesoría)")
    try:
        s1 = ReservaSala("Sala A",           costo_base=50_000)
        s2 = AlquilerEquipo("Proyector 4K",  costo_base=30_000)
        s3 = Asesoria("Asesoría Avanzada",   costo_base=80_000, asesor="Carlos Ruiz")
        sistema.servicios.extend([s1, s2, s3])
        for s in [s1, s2, s3]:
            print(f"   {s.mostrar_info()}")
    except ErrorValidacion as e:
        print(f"  ✗ {e}")

    # ----------------------------------------------------------
    # OP 5 — Servicio con costo negativo (error esperado)
    # ----------------------------------------------------------
    print("\n[OP 5] Crear servicio con costo negativo")
    try:
        s_malo = ReservaSala("Sala inválida", costo_base=-500)
    except ErrorValidacion as e:
        print(f"  ✗ Error esperado capturado: {e}")

    # ----------------------------------------------------------
    # OP 6 — Reserva de sala con descuento 10% + impuesto 8%
    # ----------------------------------------------------------
    print("\n[OP 6] Reservar sala | 3 horas | desc. 10% + imp. 8%")
    try:
        r1 = Reserva(c1, s1, 3)
        resultado = r1.procesar(descuento=0.10, impuesto=0.08)
        sistema.reservas.append(r1)
        print(f"  {resultado}")
    except ErrorReserva as e:
        print(f"  ✗ {e}")

    # ----------------------------------------------------------
    # OP 7 — Reserva con duración 0 (error esperado)
    # ----------------------------------------------------------
    print("\n[OP 7] Reservar equipo con duración 0")
    try:
        r2 = Reserva(c1, s2, 0)       # Debe fallar en __init__
        r2.procesar()
    except ErrorReserva as e:
        print(f"  ✗ Error esperado capturado: {e}")
        if e.__cause__:
            print(f"     Causa original: {e.__cause__}")

    # ----------------------------------------------------------
    # OP 8 — Reservar servicio desactivado (error esperado)
    # ----------------------------------------------------------
    print("\n[OP 8] Reservar servicio marcado como no disponible")
    try:
        s2.disponible = False
        r3 = Reserva(c1, s2, 2)
    except ErrorReserva as e:
        print(f"  ✗ Error esperado capturado: {e}")
        if e.__cause__:
            print(f"     Causa original: {e.__cause__}")
    finally:
        s2.disponible = True   # Reactivamos para operaciones siguientes

    # ----------------------------------------------------------
    # OP 9 — Reserva de asesoría sin descuento ni impuesto
    # ----------------------------------------------------------
    print("\n[OP 9] Reservar asesoría | 2 sesiones | sin ajustes")
    try:
        r4 = Reserva(c1, s3, 2)
        resultado = r4.procesar()    # Sobrecarga: sin parámetros
        sistema.reservas.append(r4)
        print(f"  {resultado}")
    except ErrorReserva as e:
        print(f"  ✗ {e}")

    # ----------------------------------------------------------
    # OP 10 — Reservar equipo y cancelar manualmente
    # ----------------------------------------------------------
    print("\n[OP 10] Reservar equipo | 4 días | luego cancelar")
    try:
        r5 = Reserva(c1, s2, 4)
        r5.procesar()               # Confirma primero
        r5.cancelar()               # Luego cancelamos manualmente
        sistema.reservas.append(r5)
        print(f"   Reserva creada y cancelada | Estado final: {r5.estado.upper()}")
    except ErrorReserva as e:
        print(f"  ✗ {e}")

    # ----------------------------------------------------------
    # RESUMEN FINAL
    # ----------------------------------------------------------
    print(f"\n{SEP}")
    print("  RESUMEN FINAL DEL SISTEMA")
    print(SEP)

    print("\n  Clientes registrados:")
    for c in sistema.clientes:
        print(f"    • {c}")

    print("\n  Servicios disponibles:")
    for s in sistema.servicios:
        print(f"    • {s.mostrar_info()}")

    print("\n  Reservas registradas:")
    for r in sistema.reservas:
        print(f"    • {r}")

    print(f"\n  Historial de {c1}:")
    historial = c1.ver_historial()
    if historial:
        for r in historial:
            print(f"    • {r}")
    else:
        print("    (sin reservas confirmadas en historial)")

    print(f"\n Simulación completada. Revisa 'logs.txt' para el registro completo.")
    print(SEP)

    return sistema


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    # 1. Ejecutar simulación automática (demuestra las 10 operaciones)
    sistema = simulacion()

    # 2. Ofrecer el menú interactivo para uso real
    print("\n¿Desea continuar con el menú interactivo? (si/no): ", end="")
    respuesta = input().strip().lower()
    if respuesta == "si":
        sistema.menu()
    else:
        print("  Sistema finalizado. ¡Hasta pronto!")
        logging.info("Usuario optó por no abrir el menú interactivo.")