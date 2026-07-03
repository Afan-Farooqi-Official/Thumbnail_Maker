import base64
from openai import AsyncOpenAI
from config import OPENAI_API_KEY

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# this is a function that uses the OpenAI Response API to generate a thumbnail image based on a prompt, style prompt, and a headshot URL. It constructs a full prompt that emphasizes the importance of keeping the likeness of the person in the headshot accurate. The function then calls the OpenAI API with the specified model and tools for image generation, and returns the generated image as raw PNG bytes. If no image generation result is found in the response, it raises a RuntimeError.
async def generate_thumbnail(prompt: str, style_prompt: str, headshot_url: str) -> bytes:
    """
    Use the Response API with gpt-image-2 as a built-in image_genertion tool. 
    Pass the headshot URL directly as an input_image.
    Returns raw PNG bytes.
    """

    full_prompt = (
        f"{style_prompt}\n\n"
        f"User request: {prompt}\n\n"
        "IMPORTANT: The generated thumbnail prominently feature the person"
        "shown in the provided reference headshot photo. Keep their likeness accurate."
    )

    response = await client.responses.create(
        model="gpt-4o",
        input = [
            {
                "role": "user",
                "content": [
                    {"type": "input_image", "url": headshot_url},
                    {"type": "text", "text": full_prompt},
                ],
            }
        ],
        tools = [
            {
                "type": "image_generation",
                "model": "gpt-image-2",
                "size": "1536x1024",
                "quality": "high",
                "output_format": "png",
            }
        ]
    )

    # Extract the base64-encoded image data from the response
    for item in response.output:
        if item.type == "image_generation_call" and item.tool_result:
            return base64.b64decode(item.tool_result)
        
    raise RuntimeError("No image generation result found in the response.")