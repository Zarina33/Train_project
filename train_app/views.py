from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Train, TrainDetail
from django.views.decorators.csrf import csrf_exempt
def landing_page(request):
    if request.user.is_authenticated:
        return redirect('train_list')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('train_list')
        else:
            return render(request, 'train_app/index.html', {'error': 'Неверное имя пользователя или пароль'})
    else:
        return render(request, 'train_app/index.html')

@login_required
def train_list_view(request):
    trains = Train.objects.order_by('-id')  # Change 'id' to '-id' for descending order
    is_admin_user = request.user.username == 'admin' or request.user.is_superuser

    if request.method == 'POST' and is_admin_user:
        train_id = request.POST.get('train_id')
        location = request.POST.get('location').strip()
        direction = request.POST.get('direction').strip()

        if train_id and location and direction:
            try:
                train = Train.objects.get(id=train_id)
                train.location = location
                train.direction = direction
                train.save()
                messages.success(request, f'Поезд {train.train_id} успешно обновлен!')
                return redirect('train_list')
            except Train.DoesNotExist:
                messages.error(request, 'Поезд не найден.')

    context = {
        'trains': trains,
        'is_admin_user': is_admin_user,
    }
    return render(request, 'train_app/train_list.html', context)



@login_required
def train_detail_view(request, train_id):
    """
    View for displaying the details of a specific train with images and serial numbers ordered by extracted timestamp.
    Includes pagination for user convenience.
    """
    train = get_object_or_404(Train, id=train_id)
    train_details = TrainDetail.objects.filter(train=train)

    # Extract timestamp and sort based on it in ascending order
    sorted_details = sorted(
        train_details,
        key=lambda detail: extract_timestamp_from_filename(detail.image_link) or datetime.min
    )

    # Paginate the sorted results
    paginator = Paginator(sorted_details, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'train': train,
        'page_obj': page_obj,
    }

    return render(request, 'train_app/train_detail.html', context)



def update_image_links():
    """
    This function updates the `image_link` paths for all TrainDetail objects in the database.
    It replaces absolute paths with relative ones that can be served via MEDIA_URL.
    """
    for detail in TrainDetail.objects.all():
        if detail.image_link.startswith('/mnt/ks/Works/railcars/railcars_new/train_project/media/'):
            detail.image_link = detail.image_link.replace(
                '/mnt/ks/Works/railcars/railcars_new/train_project/media/', '/media/')
            detail.save()


def is_admin_user(user):
    """
    Helper function to check if the user is an admin or superuser.
    """
    return user.is_superuser or user.username == 'admin'

@user_passes_test(lambda u: u.is_superuser or u.username == 'admin')
def train_detail_admin_view(request, train_id):
    train = get_object_or_404(Train, id=train_id)
    train_details = TrainDetail.objects.filter(train=train)

    # Проверьте, что данные выбраны
    print("Train details count:", train_details.count())
    
    # Проверка работы функции сортировки
    sorted_details = sorted(
        train_details,
        key=lambda detail: extract_timestamp_from_filename(detail.image_link) or datetime.min
    )
    
    print("Sorted details count:", len(sorted_details))
    
    # Проверка работы пагинации
    paginator = Paginator(sorted_details, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    print("Page object items count:", len(page_obj.object_list))

    # Обработка POST-запроса для удаления или обновления записей
    if request.method == 'POST':
        detail_id = request.POST.get('detail_id')
        serial_number = request.POST.get('serial_number', '').strip()
        delete_image = request.POST.get('delete_image', False)

        if detail_id:
            try:
                detail = TrainDetail.objects.get(id=detail_id)
                if delete_image == 'delete':
                    detail.delete()
                    messages.success(request, 'Train detail успешно удален.')
                else:
                    detail.serial_number = serial_number
                    detail.save()
                    messages.success(request, 'Train detail успешно обновлен.')
                
                # Перенаправление на текущую страницу с учетом пагинации
                return redirect(f'{request.path}?page={page_number}')
            except TrainDetail.DoesNotExist:
                messages.error(request, 'Train detail не найден.')

    # Контекст для шаблона
    context = {
        'train': train,
        'page_obj': page_obj,
    }
    return render(request, 'train_app/train_detail_admin.html', context)


@login_required
def train_details_list_view(request):
    """
    View for displaying the list of all train details.
    """
    unique_details_list = TrainDetail.objects.select_related('train').all()
    context = {
        'unique_details': unique_details_list,
    }
    return render(request, 'train_app/train_details_list.html', context)

def logout_view(request):
    """
    Log out the user and redirect to the landing page.
    """
    logout(request)
    return redirect('landing_page')
from django.http import JsonResponse

@login_required
def get_image_link_by_id(request, detail_id):
    """
    Returns the image link for a given TrainDetail object based on its ID.
    """
    try:
        # Fetch the TrainDetail object by its ID
        train_detail = get_object_or_404(TrainDetail, id=detail_id)
        # Return the image link as a JSON response
        return JsonResponse({'image_link': train_detail.image_link})
    except TrainDetail.DoesNotExist:
        # Return an error if the object is not found
        return JsonResponse({'error': 'TrainDetail not found'}, status=404)

from datetime import datetime
import re

def extract_timestamp_from_filename(image_link):
    """
    Extracts the timestamp from the image filename.
    Example format: /media/001_20241002081011_[A][0@0][0].jpg -> 2024-10-02 08:10:11
    """
    # Regular expression to match the date and time pattern in the filename
    match = re.search(r'_(\d{8})(\d{6})_', image_link)
    if match:
        date_str = match.group(1)  # e.g., "20241002"
        time_str = match.group(2)  # e.g., "081011"

        # Combine and parse the date and time strings
        timestamp_str = f"{date_str} {time_str}"
        return datetime.strptime(timestamp_str, "%Y%m%d %H%M%S")
    return None  # Return None if the pattern does not match

from django.utils import timezone

@csrf_exempt
def delete_train_data(request):
    if request.method == "POST":
        confirm_delete = request.POST.get("confirm_delete")
        if confirm_delete:
            # Получаем дату и точное время начала и конца
            date_str = request.POST.get("date")
            start_time_str = request.POST.get("start_time")
            end_time_str = request.POST.get("end_time")

            # Создаем точные временные метки для фильтрации
            try:
                start_datetime = timezone.make_aware(datetime.strptime(f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M:%S"))
                end_datetime = timezone.make_aware(datetime.strptime(f"{date_str} {end_time_str}", "%Y-%m-%d %H:%M:%S"))
            except ValueError as e:
                messages.error(request, f"Invalid date or time format: {e}")
                return redirect('delete_train_data')

            # Находим записи Train, которые соответствуют заданной дате
            trains_on_date = Train.objects.filter(date=date_str)

            # Отладочный вывод
            print(f"Начало: {start_datetime}, Конец: {end_datetime}")
            print(f"Найдено поездов на дату {date_str}: {len(trains_on_date)}")

            details_to_delete = []
            for train in trains_on_date:
                for detail in train.details.all():
                    timestamp = extract_timestamp_from_filename(detail.image_link)
                    # Преобразование `timestamp` в offset-aware формат, если это необходимо
                    if timestamp and timezone.is_naive(timestamp):
                        timestamp = timezone.make_aware(timestamp)
                    # Отладочный вывод
                    print(f"Обработка {detail.serial_number}, timestamp: {timestamp}")
                    if timestamp and start_datetime <= timestamp <= end_datetime:
                        details_to_delete.append(detail)
                        print(f"Добавлено к удалению: {detail.serial_number}")

            # Удаляем только отфильтрованные записи
            for detail in details_to_delete:
                detail.delete()
                print(f"Удалено: {detail.serial_number}")

            messages.success(request, "Entries successfully deleted.")
            return redirect('train_list')

    return render(request, 'train_app/delete_train_data.html')
