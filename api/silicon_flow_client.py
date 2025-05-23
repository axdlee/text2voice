import requests
import base64
from typing import Dict, Any, List, Optional
from api.base_client import BaseTTSClient

class SiliconFlowClient(BaseTTSClient):
    """硅基流动 API 客户端"""
    
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
        super().__init__(api_key, api_url or "https://api.siliconflow.cn/v1")
        self.headers = {"Authorization": f"Bearer {api_key}"}
        
    def create_speech(self, text: str, **kwargs) -> bytes:
        """实现文本转语音"""
        try:
            url = f"{self.base_url}/audio/speech"
            self.logger.info(f"开始文本转语音请求: {text[:50]}...")
            
            headers = {**self.headers, "Content-Type": "application/json"}
            
            data = {
                "model": kwargs.get('model', self.DEFAULT_MODEL),
                "input": text,
                "voice": kwargs.get('voice_id') or self.DEFAULT_VOICES[kwargs.get('model', self.DEFAULT_MODEL)][0],
                "response_format": kwargs.get('response_format', "mp3"),
                #"sample_rate": int(kwargs.get('sample_rate', 32000)),
                "stream": True,
                "speed": float(kwargs.get('speed', 1.0)),
                "gain": float(kwargs.get('gain', 0.0))
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            self.logger.error("API请求失败", exc_info=True)
            raise
            
    def get_voice_list(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取可用音色列表"""
        try:
            url = f"{self.base_url}/audio/voice/list"
            self.logger.info("获取音色列表...")
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            self.logger.debug(f"获取到音色列表: {result}")
            return result
            
        except Exception as e:
            self.logger.error("获取音色列表失败", exc_info=True)
            raise
            
    def delete_voice(self, voice_id: str) -> Dict[str, Any]:
        """删除指定音色"""
        try:
            url = f"{self.base_url}/audio/voice/deletions"
            self.logger.info(f"删除音色: {voice_id}")
            
            response = requests.post(
                url,
                headers=self.headers,
                json={"uri": voice_id}
            )
            response.raise_for_status()
            
            result = response.json()
            self.logger.debug(f"删除音色结果: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"删除音色失败: {voice_id}", exc_info=True)
            raise
            
    def upload_voice(self, audio_data: bytes, model: str, 
                    custom_name: str, text: str) -> Dict[str, Any]:
        """上传自定义音色
        Args:
            audio_data: 音频数据
            model: 模型ID
            custom_name: 音色名称
            text: 音频对应的文本内容
        """
        try:
            # 检查模型是否存在
            if model not in self.AVAILABLE_MODELS:
                raise ValueError(f"模型 {model} 不存在")
            
            # 根据文档修正URL
            url = f"{self.base_url}/uploads/audio/voice"
            
            # 将音频数据转换为base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            audio_data_uri = f"data:audio/mpeg;base64,{audio_base64}"
            
            # 准备请求数据
            data = {
                'audio': audio_data_uri,
                'model': model,
                'customName': custom_name,
                'text': text
            }
            
            # 添加调试日志
            self.logger.debug(f"上传音色请求参数: model={model}, customName={custom_name}, text={text}")
            self.logger.debug(f"音频数据大小: {len(audio_data)} bytes")
            
            # 发送请求
            headers = {
                **self.headers,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                url, 
                headers=headers,
                json=data  # 使用 json 参数发送 JSON 数据
            )
            
            # 如果是 400 错误，记录响应内容
            if response.status_code == 400:
                self.logger.error(f"服务器返回错误: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            self.logger.debug(f"上传音色结果: {result}")
            return result
            
        except Exception as e:
            self.logger.error("上传音色失败", exc_info=True)
            raise
            
    def get_available_models(self) -> Dict[str, str]:
        """获取可用模型列表"""
        return self.AVAILABLE_MODELS
        
    def get_default_voices(self, model: str) -> List[str]:
        """获取指定模型的默认音色"""
        return self.DEFAULT_VOICES.get(model, []) 