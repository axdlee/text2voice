from typing import Optional, Dict, Any
from utils.logger import get_child_logger
from api.client_factory import TTSClientFactory

class TTSService:
    """文本转语音服务"""
    def __init__(self, api_key: str, api_url: Optional[str] = None):
        self.logger = get_child_logger('tts_service')
        self.client = TTSClientFactory.create_client('silicon_flow', api_key, api_url)
        
    def convert_text(self, text: str, params: Dict[str, Any]) -> bytes:
        """转换文本到语音"""
        self.logger.info(f"开始转换文本: {text[:50]}...")
        return self.client.create_speech(
            text=text,
            voice_id=params.get('voice_id'),
            model=params.get('model'),
            response_format=params.get('response_format', 'mp3'),
            sample_rate=params.get('sample_rate', 32000),
            speed=params.get('speed', 1.0),
            gain=params.get('gain', 0.0)
        )
        
    def get_voices(self, model: str = None) -> Dict[str, Any]:
        """获取指定模型的音色列表"""
        try:
            self.logger.info(f"获取音色列表, 模型: {model}")
            response = self.client.get_voice_list()
            
            if not isinstance(response, dict):
                self.logger.error(f"获取音色列表返回格式错误: {response}")
                return {'result': []}
            
            if model:
                # 如果指定了模型，只返回该模型的音色
                filtered_voices = [
                    v for v in response.get('result', [])
                    if v.get('model') == model
                ]
                return {'result': filtered_voices}
            
            return response
        except Exception as e:
            self.logger.error("获取音色列表失败", exc_info=True)
            return {'result': []}
        
    def delete_voice(self, voice_id: str) -> Dict[str, Any]:
        """删除音色"""
        self.logger.info(f"删除音色: {voice_id}")
        return self.client.delete_voice(voice_id)
        
    def upload_voice(self, voice_name: str, model: str, audio_data: bytes, text: str):
        """上传自定义音色
        Args:
            voice_name: 音色名称
            model: 模型ID
            audio_data: 音频数据
            text: 音频对应的文本内容
        """
        self.logger.info(f"上传音色: {voice_name}")
        return self.client.upload_voice(
            voice_name=voice_name,
            model=model,
            audio_data=audio_data,
            text=text
        ) 