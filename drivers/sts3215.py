import serial
import time

class ServoDriver:
    def __init__(self, port='/dev/ttyUSB0', baudrate=1000000):
        try:
            self.serial = serial.Serial(port, baudrate, timeout=0.05)
            print(f"✅ 串口已打开: {port} @ {baudrate}")
        except Exception as e:
            print(f"❌ 串口打开失败: {e}")
            self.serial = None

    def close(self):
        if self.serial:
            self.serial.close()

    def enable_torque(self, id, enable=1):
        """
        强制开启/关闭舵机扭矩 (锁死/放松)
        enable: 1=锁死(变硬), 0=放松(变软)
        """
        if not self.serial: return
        
        # 寄存器 0x28 (Torque Limit/Switch)
        length = 4 
        instruction = 0x03 # Write
        reg_addr = 0x28
        val = 1 if enable else 0
        
        check_sum = (~(id + length + instruction + reg_addr + val)) & 0xFF
        packet = [0xFF, 0xFF, id, length, instruction, reg_addr, val, check_sum]
        
        try:
            self.serial.write(bytearray(packet))
            time.sleep(0.01)
        except: pass

    def write_pos(self, id, position, speed=0):
        """
        控制舵机转动
        """
        if not self.serial: return
        
        position = max(0, min(4096, int(position)))
        speed = max(0, min(3000, int(speed)))
        
        pos_L = position & 0xFF
        pos_H = (position >> 8) & 0xFF
        spd_L = speed & 0xFF
        spd_H = (speed >> 8) & 0xFF
        
        length = 7
        instruction = 0x03 # Write
        
        check_sum = (~(id + length + instruction + 0x2A + pos_L + pos_H + spd_L + spd_H)) & 0xFF
        packet = [0xFF, 0xFF, id, length, instruction, 0x2A, pos_L, pos_H, spd_L, spd_H, check_sum]
        
        try:
            self.serial.write(bytearray(packet))
        except: pass

    def read_pos(self, id):
        """
        读取舵机当前位置 (修复版核心功能)
        """
        if not self.serial: return -1
        
        try:
            # 清空缓存，防止读到旧数据
            self.serial.flushInput()
            
            # 构造读取指令: Read (0x02)
            # 读取 0x38 (Present Position) 寄存器，读 2 个字节
            # FF FF ID 04 02 38 02 Checksum
            length = 4
            instruction = 0x02 # Read
            reg_addr = 0x38    # 当前位置寄存器
            read_len = 2       # 读2字节
            
            check_sum = (~(id + length + instruction + reg_addr + read_len)) & 0xFF
            packet = [0xFF, 0xFF, id, length, instruction, reg_addr, read_len, check_sum]
            
            self.serial.write(bytearray(packet))
            # 增加一点等待时间，确保数据传回
            time.sleep(0.005) 
            
            if self.serial.in_waiting >= 8:
                response = self.serial.read(8)
                
                # 校验头 FF FF
                if response[0] == 0xFF and response[1] == 0xFF:
                    # STS 协议返回: FF FF ID Len Err P1 P2 Check
                    # P1(低位)=response[5], P2(高位)=response[6]
                    pos_L = response[5]
                    pos_H = response[6]
                    current_pos = (pos_H << 8) + pos_L
                    
                    if current_pos > 4096: return -1
                    return current_pos
        except:
            pass
            
        return -1
