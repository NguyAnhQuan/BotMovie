import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# API bot Telegram
API_TOKEN = ''

# Biến lưu trữ thông tin tạm thời giữa các bước
user_selections = {}
user_movie_selection = {}

# Hàm tìm kiếm phim
def search_movie(movie_name, limit=5):
    url = f"https://phimapi.com/v1/api/tim-kiem?keyword={movie_name}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    
    if data["status"] == "success" and data["data"]["items"]:
        return data["data"]["items"]
    return []

# Hàm lấy link phim
def get_movie_link(slug):
    url = f"https://phimapi.com/phim/{slug}"
    response = requests.get(url)
    data = response.json()
    
    if data["status"] and data["movie"]:
        return data["movie"], data["episodes"]
    return None, None

# Hàm lấy các phim gợi ý
def get_suggested_movies():
    url = "https://phimapi.com/danh-sach/phim-moi-cap-nhat?page=1"
    response = requests.get(url)
    data = response.json()
    
    if data["status"] and data["items"]:
        return data["items"]
    return []

# Hàm lấy link embed của phim gợi ý
def get_suggested_movie_links(slug):
    movie, episodes = get_movie_link(slug)
    if movie and episodes:
        return [episode['link_embed'] for episode in episodes[0]["server_data"]]
    return []

# Hàm xử lý khi người dùng gửi tên phim
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movie_name = update.message.text
    movies = search_movie(movie_name)
    
    if movies:
        # Lưu danh sách phim cho người dùng
        user_selections[update.message.from_user.id] = movies
        
        # Lấy thông tin phim đầu tiên
        selected_movie = movies[0]
        movie_info, episodes = get_movie_link(selected_movie['slug'])
        
        if movie_info and episodes:
            response_message = f"Phim: {movie_info['name']}\nNội dung: {movie_info['content']}\nChất lượng: {movie_info['quality']}\n\nCác tập phim:\n"
            
            # Gửi hình ảnh
            if 'poster_url' in movie_info:
                await update.message.reply_photo(photo=movie_info['poster_url'])
            
            # Hiển thị các link server_data cho các tập phim
            for idx, episode in enumerate(episodes[0]["server_data"], 1):
                response_message += f"{idx}. {episode['name']}: {episode['link_embed']}\n"
            
            await update.message.reply_text(response_message)
        else:
            await update.message.reply_text("Không tìm thấy thông tin chi tiết về phim.")
    else:
        # Không tìm thấy phim, cung cấp các phim gợi ý
        suggested_movies = get_suggested_movies()
        
        for movie in suggested_movies[:5]:
            # Lấy link embed của từng phim gợi ý
            movie_links = get_suggested_movie_links(movie['slug'])
            
            if movie_links:
                # Gửi hình ảnh của phim
                if 'poster_url' in movie:
                    await update.message.reply_photo(photo=movie['poster_url'])
                
                # Gửi tin nhắn với tiêu đề và link
                response_message = f"Phim: {movie['name']}\nLink: {movie_links[0]}"
                await update.message.reply_text(response_message)

# Hàm xử lý khi người dùng chọn số thứ tự phim
async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    selection = update.message.text
    
    # Kiểm tra nếu người dùng đã gửi yêu cầu tìm kiếm phim trước đó
    if user_id in user_selections:
        try:
            movie_index = int(selection) - 1  # Người dùng chọn từ 1-5, nhưng list bắt đầu từ 0
            if 0 <= movie_index < len(user_selections[user_id]):
                selected_movie = user_selections[user_id][movie_index]
                
                # Lưu thông tin phim đã chọn
                user_movie_selection[user_id] = selected_movie
                
                # Lấy thông tin chi tiết của phim đã chọn
                movie_info, episodes = get_movie_link(selected_movie['slug'])
                
                if movie_info and episodes:
                    response_message = f"Phim: {movie_info['name']}\nNội dung: {movie_info['content']}\nChất lượng: {movie_info['quality']}\n\nCác tập phim:\n"
                    
                    # Gửi hình ảnh
                    if 'poster_url' in movie_info:
                        await update.message.reply_photo(photo=movie_info['poster_url'])
                    
                    # Hiển thị các link server_data cho các tập phim
                    for idx, episode in enumerate(episodes[0]["server_data"], 1):
                        response_message += f"{idx}. {episode['name']}: {episode['link_embed']}\n"
                    
                    await update.message.reply_text(response_message)
                else:
                    await update.message.reply_text("Không tìm thấy thông tin chi tiết về phim.")
            else:
                await update.message.reply_text("Lựa chọn không hợp lệ, vui lòng chọn số từ 1 đến 5.")
        except ValueError:
            await update.message.reply_text("Vui lòng nhập số hợp lệ từ 1 đến 5.")
    else:
        await update.message.reply_text("Bạn cần tìm phim trước khi chọn.")

# Hàm bắt đầu bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chào bạn! Hãy gửi tên phim để tìm kiếm.")

# Cấu hình bot Telegram
def main():
    application = Application.builder().token(API_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Regex("^[1-5]$"), handle_selection))

    application.run_polling()

if __name__ == '__main__':
    main()
