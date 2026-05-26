import re

def get_cpu_info():
    """Получает информацию о CPU из /proc/cpuinfo (Linux)"""
    cpu_info = {}
    
    try:
        with open('/proc/cpuinfo', 'r') as f:
            content = f.read()
        
        # Количество ядер
        cpu_info['core_count'] = len(re.findall(r'^processor\s*:', content, re.MULTILINE))
        
        # Модель CPU
        model_match = re.search(r'^model name\s*:\s*(.+)$', content, re.MULTILINE)
        if model_match:
            cpu_info['model_name'] = model_match.group(1).strip()
        
        # Частота (в МГц) — может быть не на всех системах
        freq_match = re.search(r'^cpu MHz\s*:\s*([\d.]+)', content, re.MULTILINE)
        if freq_match:
            freq_mhz = float(freq_match.group(1))
            cpu_info['max_frequency_ghz'] = round(freq_mhz / 1000, 2)
        
        # Если частота не найдена, пробуем узнать из cpuinfo_max_freq
        if 'max_frequency_ghz' not in cpu_info:
            import os
            for cpu in range(cpu_info.get('core_count', 1)):
                try:
                    path = f'/sys/devices/system/cpu/cpu{cpu}/cpufreq/cpuinfo_max_freq'
                    if os.path.exists(path):
                        with open(path, 'r') as f:
                            freq_khz = int(f.read().strip())
                            cpu_info['max_frequency_ghz'] = round(freq_khz / 1e6, 2)
                            break
                except:
                    continue
                    
    except Exception as e:
        print(f"Error reading CPU info: {e}")
        cpu_info['core_count'] = 4  # fallback
        cpu_info['model_name'] = 'Unknown CPU'
    
    return cpu_info