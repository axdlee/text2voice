import requests
import json
import os
from typing import Optional, Dict, Any
from utils.logger import logger

class SiliconFlowClient:
    DEFAULT_MODEL = "FunAudioLLM/CosyVoice2-0.5B"
    AVAILABLE_MODELS = {
        "fishaudio/fish-speech-1.5": "Fish-Speech-1.5 (充值余额付费)",
        "fishaudio/fish-speech-1.4": "Fish-Speech-1.4 (充值余额付费)",
        "FunAudioLLM/CosyVoice2-0.5B": "CosyVoice2-0.5B (赠送余额付费)",
        "RVC-Boss/GPT-SoVITS": "GPT-SoVITS (赠送余额付费)"
    }
    
    DEFAULT_VOICES = {
        "fishaudio/fish-speech-1.5": [
            "fishaudio/fish-speech-1.5:alex",
            "fishaudio/fish-speech-1.5:anna",
            "fishaudio/fish-speech-1.5:bella",
            "fishaudio/fish-speech-1.5:benjamin",
            "fishaudio/fish-speech-1.5:charles",
            "fishaudio/fish-speech-1.5:claire",
            "fishaudio/fish-speech-1.5:david",
            "fishaudio/fish-speech-1.5:diana"
        ],
        "fishaudio/fish-speech-1.4": [
            "fishaudio/fish-speech-1.4:alex",
            "fishaudio/fish-speech-1.4:anna",
            "fishaudio/fish-speech-1.4:bella",
            "fishaudio/fish-speech-1.4:benjamin",
            "fishaudio/fish-speech-1.4:charles",
            "fishaudio/fish-speech-1.4:claire",
            "fishaudio/fish-speech-1.4:david",
            "fishaudio/fish-speech-1.4:diana"
        ],
        "FunAudioLLM/CosyVoice2-0.5B": [
            "FunAudioLLM/CosyVoice2-0.5B:alex",
            "FunAudioLLM/CosyVoice2-0.5B:anna",
            "FunAudioLLM/CosyVoice2-0.5B:bella",
            "FunAudioLLM/CosyVoice2-0.5B:benjamin",
            "FunAudioLLM/CosyVoice2-0.5B:charles",
            "FunAudioLLM/CosyVoice2-0.5B:claire",
            "FunAudioLLM/CosyVoice2-0.5B:david",
            "FunAudioLLM/CosyVoice2-0.5B:diana"
        ],
        "RVC-Boss/GPT-SoVITS": [
            "RVC-Boss/GPT-SoVITS:alex",
            "RVC-Boss/GPT-SoVITS:anna",
            "RVC-Boss/GPT-SoVITS:bella",
            "RVC-Boss/GPT-SoVITS:benjamin",
            "RVC-Boss/GPT-SoVITS:charles",
            "RVC-Boss/GPT-SoVITS:claire",
            "RVC-Boss/GPT-SoVITS:david",
            "RVC-Boss/GPT-SoVITS:diana"
        ]
    }
    
    def __init__(self, api_key: str, api_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = api_url or "https://api.siliconflow.cn/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}"
        }
        self.logger = logger.getChild('api')
        self.logger.info("初始化 API 客户端...")
        self.logger.debug(f"API Base URL: {self.base_url}")
        # 隐藏 API Key 的大部分内容
        masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
        self.logger.debug(f"API Key: {masked_key}")
        
    def create_speech(self, text: str, voice_id: Optional[str] = None, model: Optional[str] = None, 
                     response_format: str = "mp3", sample_rate: int = 32000, 
                     speed: float = 1, gain: float = 0) -> Dict[str, Any]:
        """将文本转换为语音"""
        try:
            url = f"{self.base_url}/audio/speech"
            self.logger.info(f"开始文本转语音请求: {text[:50]}...")
            self.logger.debug(f"完整请求文本: {text}")
            
            headers = self.headers.copy()
            headers["Content-Type"] = "application/json"
            
            selected_model = model or self.DEFAULT_MODEL
            self.logger.info(f"使用模型: {selected_model}")
            
            data = {
                "model": selected_model,
                "input": text,
                "voice": voice_id or self.DEFAULT_VOICES[selected_model][0],
                "response_format": response_format,
                "sample_rate": int(sample_rate),
                "stream": True,
                "speed": float(speed),
                "gain": float(gain)
            }
            
            self.logger.debug(f"请求参数: {data}")
            self.logger.debug(f"请求头: {headers}")
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                self.logger.error(f"API请求失败 (状态码: {response.status_code})")
                self.logger.error(f"错误响应: {response.text}")
                self.logger.error(f"请求URL: {url}")
                self.logger.error(f"请求数据: {data}")
                response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            self.logger.debug(f"响应Content-Type: {content_type}")
            
            if content_type.startswith('audio/'):
                self.logger.info(f"成功获取音频数据 ({len(response.content)} 字节)")
                return response.content
            
            json_response = response.json()
            self.logger.debug(f"API响应: {json_response}")
            return json_response
            
        except requests.exceptions.RequestException as e:
            self.logger.error("API请求异常", exc_info=True)
            self.logger.error(f"请求URL: {url}")
            self.logger.error(f"请求参数: {data}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"错误响应: {e.response.text}")
            raise
        except Exception as e:
            self.logger.error("未预期的错误", exc_info=True)
            raise
        
    def get_voice_list(self) -> Dict[str, Any]:
        """获取可用的语音列表"""
        try:
            url = f"{self.base_url}/audio/voice/list"
            self.logger.info("获取音色列表...")
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                self.logger.error(f"获取音色列表失败 (状态码: {response.status_code})")
                self.logger.error(f"错误响应: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            voice_count = len(result.get('result', []))
            self.logger.info(f"成功获取音色列表: {voice_count} 个音色")
            self.logger.debug(f"音色列表详情: {result}")
            return result
            
        except Exception as e:
            self.logger.error("获取音色列表失败", exc_info=True)
            self.logger.error(f"请求URL: {url}")
            raise
        
    def delete_voice(self, voice_id: str) -> Dict[str, Any]:
        """删除指定的语音"""
        try:
            url = f"{self.base_url}/audio/voice/deletions"
            self.logger.info(f"删除音色: {voice_id}")
            
            response = requests.post(url, 
                                   headers=self.headers, 
                                   json={"uri": voice_id})
            
            if response.status_code != 200:
                self.logger.error(f"删除音色失败 (状态码: {response.status_code})")
                self.logger.error(f"错误响应: {response.text}")
                self.logger.error(f"音色ID: {voice_id}")
                response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"音色删除成功: {voice_id}")
            self.logger.debug(f"删除响应: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"删除音色失败: {voice_id}", exc_info=True)
            self.logger.error(f"请求URL: {url}")
            raise
        
    def upload_voice(self, audio: str, model: str, customName: str, text: str) -> Dict[str, Any]:
        """上传语音文件"""
        try:
            url = f"{self.base_url}/uploads/audio/voice"
            self.logger.info(f"开始上传音色: {customName}")
            self.logger.debug(f"模型: {model}")
            self.logger.debug(f"音频长度: {len(audio)} 字符")
            self.logger.debug(f"文本: {text}")
            
            files = {
                'audio': (None, audio),
                'model': (None, model),
                'customName': (None, customName),
                'text': (None, text)
            }
            
            response = requests.post(url, headers=self.headers, files=files)
            
            if response.status_code != 200:
                self.logger.error(f"上传音色失败 (状态码: {response.status_code})")
                self.logger.error(f"错误响应: {response.text}")
                self.logger.error(f"请求参数: {files}")
                response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"音色上传成功: {customName}")
            self.logger.debug(f"上传响应: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"上传音色失败: {customName}", exc_info=True)
            self.logger.error(f"请求URL: {url}")
            self.logger.error(f"请求参数: {files}")
            raise
        
    def create_transcription(self, file_path: str) -> Dict[str, Any]:
        """
        创建音频转写
        """
        url = f"{self.base_url}/audio/transcriptions"
        files = {
            'file': open(file_path, 'rb')
        }
        data = {
            'model': 'FunAudioLLM/SenseVoiceSmall'
        }
        response = requests.post(url, headers=self.headers, data=data, files=files)
        response.raise_for_status()
        return response.json() 