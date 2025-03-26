import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import json

# Set page config
st.set_page_config(page_title="Auto Repair Request Classifier", layout="wide")

# Define the repair categories from the screenshots
REPAIR_CATEGORIES = {
    "Кузовные работы и детейлинг": ["кузов", "крыло", "бампер", "покраска", "вмятина", "царапина", "полировка", "детейлинг"],
    "Ремонт/замена двигателя и навесного": ["двигатель", "мотор", "троит", "стук", "перегрев", "масло", "свечи", "цилиндр", "поршень", "ремень грм", "навесного"],
    "Автоэлектрики/компьют.диагностика": ["электрика", "проводка", "аккумулятор", "фары", "лампочки", "генератор", "стартер", "бортовой компьютер", "диагностика"],
    "Ремонт ходовой/подвески/геометрия": ["ходовая", "подвеска", "амортизаторы", "рессоры", "стойки", "стабилизатор", "стук при езде", "вибрация", "геометрия"],
    "Трансмиссия АКПП/МКПП/Вариатор": ["коробка", "трансмиссия", "сцепление", "акпп", "мкпп", "вариатор", "передачи", "переключение"],
    "Ремонт печка/кондиционер/радиатор": ["печка", "кондиционер", "радиатор", "отопитель", "климат"],
    "Ремонт топливной системы": ["топливо", "бензин", "инжектор", "карбюратор", "бензонасос", "форсунки"],
    "Рулевой механизм": ["руль", "рулевая рейка", "гур", "гидроусилитель"],
    "Сварочные/токарные работы": ["сварка", "сварочные", "токарные"],
    "Ремонт стекол": ["стекло", "лобовое", "заднее", "боковое", "трещина"],
    "Выхлопная система/Ремонт турбин": ["выхлоп", "глушитель", "катализатор", "турбина"],
    "Чип тюнинг": ["чип", "тюнинг", "прошивка", "мощность"],
    "Ремонт стартера / генератора": ["стартер", "генератор"],
    "Замена масла и жидкостей": ["масло", "антифриз", "тормозная жидкость", "жидкость гур", "замена масла", "фильтр"],
    "Установка газа на авто": ["газ", "гбо", "газобаллонное", "метан", "пропан"]
}

# Setup the LLM classification system
def setup_langchain():
    """Set up the LangChain components for classification."""
    
    # Create the prompt template - fixed to avoid StructuredOutputParser error
    template = """
    Ты - эксперт автомеханической классификационной системы. Твоя работа - определить, к какой категории ремонта относится заявка клиента.
    
    Доступные категории ремонта:
    {categories}
    
    Заявка клиента:
    {request}
    
    Определи наиболее подходящую категорию ремонта. Если заявка неоднозначна или может относиться к нескольким категориям, выбери самую актуальную.
    
    Верни ответ в следующем формате JSON:
    {{
        "category": "Название категории из списка выше",
        "confidence": число от 0 до 1,
        "explanation": "Краткое объяснение, почему была выбрана эта категория"
    }}
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # Use the OpenAI model with enhanced temperature for better Russian language handling
    llm = ChatOpenAI(temperature=0.1, model_name="gpt-3.5-turbo-16k")
    
    # Use a simple string output parser instead of the StructuredOutputParser 
    # that was causing the error
    output_parser = StrOutputParser()
    
    return llm, prompt, output_parser

def process_llm_response(response_text):
    """Process the LLM response and extract the classification data."""
    try:
        # Try to parse the JSON response
        result = json.loads(response_text)
        return result
    except Exception as e:
        st.error(f"Ошибка при обработке ответа: {e}")
        return {"category": "Неизвестно", "confidence": 0, "explanation": "Не удалось обработать ответ"}

def classify_repair_request(request, llm, prompt, output_parser):
    """Classify the repair request using LangChain."""
    
    # Format the categories for the prompt - sorted by name for better readability
    categories_str = "\n".join([f"- {cat}" for cat in sorted(REPAIR_CATEGORIES.keys())])
    
    # Format the prompt
    formatted_prompt = prompt.format(
        categories=categories_str,
        request=request
    )
    
    # Get the response from the LLM
    response = llm.invoke(formatted_prompt)
    
    # Parse the response with the string output parser
    raw_response = output_parser.invoke(response)
    
    # Process the raw string response into structured data
    result = process_llm_response(raw_response)
    
    return result

def get_api_key():
    """Get the OpenAI API key from the environment or from the user."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        api_key = st.sidebar.text_input("Введите ваш API ключ OpenAI", type="password")
    return api_key

def main():
    st.title("🚗 Автоматическая классификация заявок на ремонт автомобилей")
    
    # Sidebar for API key
    api_key = get_api_key()
    if not api_key:
        st.warning("Пожалуйста, введите ваш API ключ OpenAI в боковой панели для работы с моделью.")
        return
    
    os.environ["OPENAI_API_KEY"] = api_key
    
    # Set up LangChain - with error handling
    try:
        llm, prompt, output_parser = setup_langchain()
    except Exception as e:
        st.error(f"Ошибка инициализации LangChain: {e}")
        return
    
    # Car selection - using the car from the screenshots
    car_models = ["Dodge", "Toyota", "Honda", "Ford", "Chevrolet", "Nissan", "Volkswagen", "Mazda", "Другое"]
    selected_car = st.selectbox("Выберите марку автомобиля", car_models)
    
    # Input form
    with st.form("repair_request_form"):
        if selected_car == "Другое":
            user_car = st.text_input("Введите марку автомобиля")
        else:
            user_car = selected_car
        
        user_request = st.text_area("Опишите проблему с автомобилем", height=150,
                                    placeholder="Например: 'Стук в двигателе при разгоне' или 'Не работает кондиционер'")
        
        submitted = st.form_submit_button("Отправить заявку")
    
    # Process the request if submitted
    if submitted and user_request:
        with st.spinner("Анализируем вашу заявку..."):
            try:
                # Classify the request
                result = classify_repair_request(user_request, llm, prompt, output_parser)
                
                # Display the results
                st.success(f"Заявка на ремонт автомобиля {user_car} была классифицирована!")
                
                # Show the classification
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Результат классификации")
                    st.write(f"**Категория ремонта:** {result['category']}")
                    st.write(f"**Уверенность:** {result['confidence']*100:.1f}%")
                    st.write(f"**Объяснение:** {result['explanation']}")
                
                with col2:
                    st.subheader("Детали заявки")
                    st.write(f"**Автомобиль:** {user_car}")
                    st.write(f"**Описание проблемы:** {user_request}")
            except Exception as e:
                st.error(f"Произошла ошибка при классификации: {e}")
    
    # Display some examples
    with st.expander("Примеры заявок"):
        st.markdown("""
        ### Примеры заявок и их классификаций:
        
        1. **Кузовные работы и детейлинг**
           - "У меня вмятина на переднем крыле после парковки"
           - "Нужна полировка и детейлинг салона"
        
        2. **Ремонт/замена двигателя и навесного**
           - "Двигатель троит и плохо заводится"
           - "Стук в двигателе при ускорении"
        
        3. **Автоэлектрики/компьют.диагностика**
           - "Не работают фары и бортовой компьютер"
           - "Аккумулятор разряжается за ночь"
        
        4. **Ремонт ходовой/подвески/геометрия**
           - "Стук в подвеске при проезде неровностей"
           - "Машину ведет в сторону при движении"
        
        5. **Замена масла и жидкостей**
           - "Нужно поменять масло и фильтры"
           - "Хочу заменить антифриз и тормозную жидкость"
        """)
        
    # About the application
    st.sidebar.header("О приложении")
    st.sidebar.info("""
    Это приложение использует искусственный интеллект для автоматической классификации заявок на ремонт автомобилей.
    
    Система анализирует текст заявки и определяет подходящую категорию ремонта, чтобы направить клиента к нужному специалисту.
    """)

if __name__ == "__main__":
    main()