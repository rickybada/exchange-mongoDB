from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, authenticate, login
from .forms import LoginForm, OrderForm, RegistrationForm
from .models import Order, Profile
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import requests


@login_required
def home_view(request):
    user = request.user
    profile = get_object_or_404(Profile, user=user)  # Più sicuro
    profile.btc_price = update_btc_price()  # Assumendo che questa funzione sia definita
    profile.save()

    orders = Order.objects.filter(profile=profile)  # Solo gli ordini relativi all'utente loggato

    context = {
        'profile': profile,
        'orders': orders,
    }

    return render(request, 'home.html', context)


@login_required
def buy_sell_view(request):
    form = OrderForm()
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Esegui le azioni necessarie per salvare l'ordine
            order = form.save(commit=False)  # Crea un'istanza dell'ordine ma non la salva ancora nel database
            user_profile = request.user.profile  # Ottieni il profilo associato all'utente corrente
            order.profile = user_profile  # Assegna il profilo all'ordine
            order.save()  # Salva ora l'ordine nel database
    
    return render(request, 'buy_sell.html', {'form': form})  


@login_required
def detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'detail.html', {'order': order})


def registration_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Creazione del profilo associato all'utente
            profile = Profile(user=user)
            profile.save()
            
            login(request, user)
            return redirect('login')
    else:
        form = RegistrationForm()
        
    return render(request, 'registration.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home.html')
            else:
                # Autenticazione fallita
                form.add_error(None, 'Username o password non corretti')
                
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})
         


def logout_view(request):
    logout(request)
    print('Hai effettuato il logout')
    return render(request, 'logout.html')


@login_required
def order_json_view(request):
    orders_json = []

    for order in Order.objects.all():
        order_dict = {
            "_id": str(order._id),
            "User": str(order.profile.user),
            "Id": order.id,
            "Type": order.get_type_display(),
            "Status": order.get_status_display(),
            "Price": order.order_price,
            "Qty": order.btc_quantity,
        }

        if order.type == 'buy':
            order_dict["Buyer"] = str(order.profile.user)
            order_dict["Profit / Loss"] = order.profile.profit_loss  # Assumendo che profit_loss sia un campo nel modello Profile
        else:
            order_dict["Seller"] = str(order.profile.user)
            order_dict["Purchase Price"] = order.profile.average_weighted

        orders_json.append(order_dict)

    return JsonResponse({'order': orders_json})


@transaction.atomic
def logic_of_exchange(request):
    profile = Profile.objects.get(user=request.user)

    # Ordini di acquisto e vendita ordinati per prezzo e poi per data
    buy_orders = Order.objects.filter(type='buy', status='open').order_by('order_price', 'datetime')
    sell_orders = Order.objects.filter(type='sell', status='open').order_by('order_price', 'datetime')

    for buy in buy_orders:
        for sell in sell_orders:
            # Se l'ordine di acquisto è maggiore o uguale a quello di vendita
            if buy.order_price >= sell.order_price:
                
                if buy.btc_quantity >= sell.btc_quantity:
                    executed_price = sell.order_price
                    # Esegui la transazione per la quantità completa
                    profile.btc_balance += sell.btc_quantity
                    profile.usd_balance -= sell.order_price
                    profile.profit_loss = sell.order_price - profile.calculate_average_weighted()
                    profile.usd_balance += profile.profit_loss
                    # Contrassegna entrambi gli ordini come chiusi
                    buy.executed_price = executed_price
                    sell.executed_price = executed_price
                    buy.status = 'closed'
                    sell.status = 'closed'
                else:
                    # Esegui la transazione per la quantità parziale
                    profile.btc_balance += buy.btc_quantity
                    profile.usd_balance -= buy.order_price
                    # Aggiorna la quantità dell'ordine di vendita
                    sell.btc_quantity -= buy.btc_quantity
                    # Contrassegna l'ordine di acquisto come chiuso
                    buy.status = 'closed'
                    
                # Salva gli ordini e il profilo
                buy.save()
                sell.save()
                profile.save()
                
                # Rompi il ciclo interno se l'ordine di acquisto è stato chiuso
                if buy.status == 'closed':
                    break


def update_btc_price():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    parameters = {'start': '1', 'limit': '2', 'convert': 'USD'}
    headers = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': '23cec648-0793-43a2-8b60-23ddbde0f138',}

    response = requests.get(url, headers=headers, params=parameters)
    data = response.json()

    # Prendi il prezzo attuale del BTC in USD (assicurati che il primo elemento sia BTC)
    btc_price = data['data'][0]['quote']['USD']['price']
    return btc_price