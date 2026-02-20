// Enum definitions

enum OrderStatus { pending, confirmed, preparing, ready, delivered, cancelled }

enum FulfillmentType { delivery, pickup }

enum SenderType { client, business, bot }

class Manager {
  final String managerId;
  final String fullName;
  final String email;
  final String? authUserId;

  Manager({
    required this.managerId,
    required this.fullName,
    required this.email,
    this.authUserId,
  });

  factory Manager.fromJson(Map<String, dynamic> json) {
    return Manager(
      managerId: json['manager_id'],
      fullName: json['full_name'],
      email: json['email'],
      authUserId: json['auth_user_id'],
    );
  }

  Map<String, dynamic> toJson() => {
    'manager_id': managerId,
    'full_name': fullName,
    'email': email,
    'auth_user_id': authUserId,
  };
}

class Business {
  final String businessId;
  final String name;
  final String? whatsappPhoneNumber;
  final String? whatsappPhoneNumberId;
  final String? address;
  final String? logoUrl;
  final bool isActive;

  String get id => businessId;

  Business({
    required this.businessId,
    required this.name,
    this.whatsappPhoneNumber,
    this.whatsappPhoneNumberId,
    this.address,
    this.logoUrl,
    this.isActive = true,
  });

  factory Business.fromJson(Map<String, dynamic> json) {
    return Business(
      businessId: json['business_id'],
      name: json['name'],
      whatsappPhoneNumber: json['whatsapp_phone_number'],
      whatsappPhoneNumberId: json['whatsapp_phone_number_id'],
      address: json['address'],
      logoUrl: json['logo_url'],
      isActive: json['is_active'] ?? true,
    );
  }

  Map<String, dynamic> toJson() => {
    'business_id': businessId,
    'name': name,
    'whatsapp_phone_number': whatsappPhoneNumber,
    'whatsapp_phone_number_id': whatsappPhoneNumberId,
    'address': address,
    'logo_url': logoUrl,
    'is_active': isActive,
  };
}

class MenuItem {
  final String itemId;
  final String businessId;
  final String name;
  final String? description;
  final String? imageUrl;
  final double price;
  final bool isAvailable;

  MenuItem({
    required this.itemId,
    required this.businessId,
    required this.name,
    this.description,
    this.imageUrl,
    required this.price,
    this.isAvailable = true,
  });

  factory MenuItem.fromJson(Map<String, dynamic> json) {
    return MenuItem(
      itemId: json['item_id'],
      businessId: json['business_id'],
      name: json['name'],
      description: json['description'],
      imageUrl: json['image_url'],
      price: double.tryParse(json['price'].toString()) ?? 0.0,
      isAvailable: json['is_available'] ?? true,
    );
  }

  Map<String, dynamic> toJson() => {
    'item_id': itemId,
    'business_id': businessId,
    'name': name,
    'description': description,
    'image_url': imageUrl,
    'price': price,
    'is_available': isAvailable,
  };
}

class Client {
  final String clientId;
  final String businessId;
  final String waId;
  final String? fullName;
  final String? phoneNumber;

  Client({
    required this.clientId,
    required this.businessId,
    required this.waId,
    this.fullName,
    this.phoneNumber,
  });

  factory Client.fromJson(Map<String, dynamic> json) {
    return Client(
      clientId: json['client_id'],
      businessId: json['business_id'],
      waId: json['wa_id'],
      fullName: json['full_name'],
      phoneNumber: json['phone_number'],
    );
  }

  Map<String, dynamic> toJson() => {
    'client_id': clientId,
    'business_id': businessId,
    'wa_id': waId,
    'full_name': fullName,
    'phone_number': phoneNumber,
  };
}

class OrderItem {
  final String? orderItemId;
  final String itemId;
  final String? nameSnapshot;
  final int quantity;
  final double unitPrice;

  OrderItem({
    this.orderItemId,
    required this.itemId,
    this.nameSnapshot,
    required this.quantity,
    required this.unitPrice,
  });

  factory OrderItem.fromJson(Map<String, dynamic> json) {
    return OrderItem(
      orderItemId: json['order_item_id'],
      itemId: json['item_id'],
      nameSnapshot: json['name_snapshot'],
      quantity: json['quantity'],
      unitPrice: double.tryParse(json['unit_price'].toString()) ?? 0.0,
    );
  }
}

class Order {
  final String orderId;
  final String? clientId;
  final String businessId;
  final double totalAmount;
  final OrderStatus status;
  final FulfillmentType deliveryType;
  final String? deliveryAddress;
  final DateTime orderedAt;
  final List<OrderItem> items;

  Order({
    required this.orderId,
    this.clientId,
    required this.businessId,
    required this.totalAmount,
    required this.status,
    required this.deliveryType,
    this.deliveryAddress,
    required this.orderedAt,
    required this.items,
  });

  factory Order.fromJson(Map<String, dynamic> json) {
    return Order(
      orderId: json['order_id'],
      clientId: json['client_id'],
      businessId: json['business_id'],
      totalAmount: double.tryParse(json['total_amount'].toString()) ?? 0.0,
      status: OrderStatus.values.firstWhere(
        (e) => e.name == json['status'],
        orElse: () => OrderStatus.pending,
      ),
      deliveryType: FulfillmentType.values.firstWhere(
        (e) => e.name == json['delivery_type'],
        orElse: () => FulfillmentType.delivery,
      ),
      deliveryAddress: json['delivery_address'],
      orderedAt: DateTime.parse(
        json['ordered_at'] ?? DateTime.now().toIso8601String(),
      ),
      items:
          (json['items'] as List?)
              ?.map((i) => OrderItem.fromJson(i))
              .toList() ??
          [],
    );
  }
}

class Conversation {
  final String conversationId;
  final String businessId;
  final String clientId;
  final String? lastMessage;
  final DateTime updatedAt;
  final String? clientName;
  final String? clientWaId;

  Conversation({
    required this.conversationId,
    required this.businessId,
    required this.clientId,
    this.lastMessage,
    required this.updatedAt,
    this.clientName,
    this.clientWaId,
  });

  Conversation copyWith({
    String? conversationId,
    String? businessId,
    String? clientId,
    String? lastMessage,
    DateTime? updatedAt,
    String? clientName,
    String? clientWaId,
  }) {
    return Conversation(
      conversationId: conversationId ?? this.conversationId,
      businessId: businessId ?? this.businessId,
      clientId: clientId ?? this.clientId,
      lastMessage: lastMessage ?? this.lastMessage,
      updatedAt: updatedAt ?? this.updatedAt,
      clientName: clientName ?? this.clientName,
      clientWaId: clientWaId ?? this.clientWaId,
    );
  }

  factory Conversation.fromJson(Map<String, dynamic> json) {
    return Conversation(
      conversationId: json['conversation_id'],
      businessId: json['business_id'],
      clientId: json['client_id'],
      lastMessage: json['last_message'],
      updatedAt: DateTime.parse(json['updated_at']),
      clientName: json['client_name'],
      clientWaId: json['client_wa_id'],
    );
  }
}

class Message {
  final String messageId;
  final String conversationId;
  final SenderType senderType;
  final String content;
  final DateTime createdAt;

  Message({
    required this.messageId,
    required this.conversationId,
    required this.senderType,
    required this.content,
    required this.createdAt,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      messageId: json['message_id'],
      conversationId: json['conversation_id'],
      senderType: SenderType.values.firstWhere(
        (e) => e.name == json['sender_type'],
        orElse: () => SenderType.client,
      ),
      content: json['content'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() => {
    'conversation_id': conversationId,
    'sender_type': senderType.name,
    'content': content,
  };
}
