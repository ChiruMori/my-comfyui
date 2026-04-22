# 我的 ComfyUI 工作流

## 此项目是做什么的

**问题**：在 ComfyUI 中下载了太多模型，磁盘要爆了

**解决**：精选一些实用的工作流，通过模型列表得到已不要的模型，然后删掉他们（简单粗暴）

**更多作用**：

- 借助 Git 将实用的工作流、模型进行版本化管理，方便使用
- 把一些工作流的效果列出来，方便使用时对比、挑选
- 工作流 json 在 ComfyUI 的 API 调用上可能有用（待测试，如果可用将在这个项目上更新）

## 图像生成

### realistic

> 注意，该模型已更新，建议使用新模型

使用 [RealVisXL](https://civitai.com/models/139562/realvisxl-v50?modelVersionId=789646) 的工作流

现实主义风格，适合风景

有手部问题，略严重

<img height="300px" src="doc/real.png" />

### SD1.5(NSFW)

使用 [cuteyukimixadorable](https://civitai.com/models/28169/cuteyukimixadorable-style) 的工作流

独特的画风，适合生成可爱卡通风格人物图片，可以访问模型页面查看更多实例

有手部问题但可控

不认识大部分 ACG 角色

BaseModel: SD 1.5

<img height="300px" src="doc/sd1.5.png" />

### Nahida(NSFW)

使用 [zukiCuteILL_v60](https://huggingface.co/John6666/zuki-cute-ill-v60-sdxl) 的工作流

不太“安全”的模型，也可用于普通的图片生成场景。该模型在C站的页面已挂，[作者的C站链接](https://civitai.com/user/ZU_KI)

画风比较可爱，适合生成可爱、卡通风格人物图片，擅长 NSFW 内容

认识大部分 ACG 角色

BaseModel: SDXL

<img height="300px" src="doc/nahida.png" />

## 图像编辑

### 区域重绘 Inpaint

使用遮罩对图像特定区域进行重绘

适合对画面少部分内容进行修复、修改、替换

不适合在重绘部分完成过于复杂的绘制任务

下图为通过遮罩引导，替换地面为落满繁花的水面的效果

<img height="300px" src="doc/inpaint.png" />

### 图像编辑 Qwen2509

通过纯提示词引导进行图像编辑，效果非常好

最多能参考三张图片，但会有混淆问题

能够进行稍复杂的编辑操作

下图为通过提示词移除图中拉门的效果

<img height="300px" src="doc/edit.png" />

### 图像去水印

通过模型自动识别水印并进行遮罩重绘以去除水印

水印识别效果尚可

重绘效果一般，可以试试其他模型来重绘

<img height="300px" src="doc/water.png" />

### 图像放大

放大4倍，简单有效，放大效果不错

<img height="300px" src="doc/up.png">

## 3D

> 3D 玩得比较少，并未发现什么好用的工作流

### 图像转3D模型

模板工作流，效果如图

<img height="300px" src="doc/3d.png" />

## 音频处理

### 音乐生成（ACE1.5）

目前 ACE1.5 的效果听上去不如 Suno 的 V3.5（更早的版本没试过），仅可用于玩一玩，并不推荐使用

开源方案中，HeartMula 3B效果更好一些（主观感受上大致相当于 Suno V3.5，7B尚未开放），但是 ComfyUI 集成不好

### 语音克隆

在一个工作流里面完成音色克隆、语音生成的全过程

克隆效果很好，比如 [**这个音频**](doc/civilization.mp3) 是使用铃兰（来自明日方舟）的音色，念文明6的开场词

## 视频处理

### Wan2.2 图生视频

模板工作流，图片+提示词生成视频

视频可能出现静止问题、诡异画面等情况（相对 Wan2.1 好多了）

生成速度较慢，不建议一次生成太长的视频

视频效果可参考：[0经费出道？给二阶堂姐妹拍了一支绝美但生草的MV](https://www.bilibili.com/video/BV18GQQBoEGx/?share_source=copy_web)（该视频为本工作流的输出，经剪辑后得到）

### Wan2.2 首尾帧视频

模板工作流，首尾帧图片+提示词生成视频

视频容易出现静止、奇怪的过渡等问题，相对 Wan2.1 有提升

16G显存设备上，`640*640` 5s 视频需要 733s，还提供了更快速的版本（质量有所下降）

以下是使用效果，中间过渡时怪怪的：

![](doc/2frame.png)

Wan2.1 首尾帧视频效果可参考：[音乐都能当编程语言了？来听听代码是什么旋律](https://www.bilibili.com/video/BV12xKWz5EnJ/?share_source=copy_web)（该视频右下角的视频为 Wan2.1 的首尾帧视频一路拼接到尾）

### hunyuan 提示词直接出视频

模板工作流，仅用提示词出视频

视频效果一般，未深入使用

<img height="300px" src="doc/hunyuan.webp" />

### 音频+图片+提示词生成视频

比较实用的一个工作流，可以让图片中的人按照配音开口说话，也是基于 Wan2.2 的工作流

真人图片的情况也可以对上口型

可以按照提示词做动作

![](doc/workflow.png)

按照 chunk 来扩展，每加一个节点拓展一个 chunk，以实现长视频生成。

但测试发现，如果生成太长的视频有可能会出现一些奇怪的情况，建议不要生成一分钟以上的视频。

[**效果视频**](doc/civilization.mp4)（使用上面的音频，加上一个绿幕铃兰图像生成）

## 使用本项目

- 克隆项目到本地
- 安装依赖（使用 `uv sync` 安装）
- 修改配置（将 `.env.example` 复制为 `.env`，并修改其中的配置）
- 运行项目（使用 `uv run src/main.py` 运行项目）

### 工作流管理

+ `python -m src.main workflow list`: 列出所有工作流
+ `python -m src.main workflow export`: 导出工作流到备份目录
+ `python -m src.main workflow import`: 导入备份目录的工作流
+ `python -m src.main workflow info XXX`: 查看工作流 XXX 引用的模型，含 VAE、LoRA（可能包含干扰项）

### 模型管理

+ `python -m src.main model scan`: 扫描模型目录，列出所有模型文件，并在通过控制台确认后删除未引用的模型文件，你有机会多次确认